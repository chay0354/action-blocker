-- Create pending_transactions table for flagged transactions awaiting approval
CREATE TABLE IF NOT EXISTS public.pending_transactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    from_user_id UUID NOT NULL,
    to_user_id UUID NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    violations JSONB, -- Array of rule violations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by UUID, -- Admin user who reviewed
    review_notes TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_pending_transactions_status ON public.pending_transactions(status);
CREATE INDEX IF NOT EXISTS idx_pending_transactions_from_user ON public.pending_transactions(from_user_id);
CREATE INDEX IF NOT EXISTS idx_pending_transactions_created_at ON public.pending_transactions(created_at DESC);

-- Enable RLS
ALTER TABLE public.pending_transactions ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Service role full access" ON public.pending_transactions;
DROP POLICY IF EXISTS "Admins can view all pending" ON public.pending_transactions;
DROP POLICY IF EXISTS "Users can view own pending" ON public.pending_transactions;

-- Create policies
CREATE POLICY "Service role full access" ON public.pending_transactions FOR ALL USING (true);
CREATE POLICY "Admins can view all pending" ON public.pending_transactions FOR SELECT USING (true);
CREATE POLICY "Users can view own pending" ON public.pending_transactions 
    FOR SELECT USING (auth.uid() = from_user_id);

-- Create rules table for managing transaction rules
CREATE TABLE IF NOT EXISTS public.transaction_rules (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    rule_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL, -- amount_threshold, repeated_transaction, etc.
    rule_config JSONB NOT NULL, -- Rule-specific configuration
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transaction_rules_enabled ON public.transaction_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_transaction_rules_rule_id ON public.transaction_rules(rule_id);

ALTER TABLE public.transaction_rules ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access" ON public.transaction_rules;
CREATE POLICY "Service role full access" ON public.transaction_rules FOR ALL USING (true);

-- Insert default rules
INSERT INTO public.transaction_rules (rule_id, name, description, rule_type, rule_config, enabled)
VALUES 
    ('amount_threshold', 'Amount Threshold', 'Flag transactions above $500', 'amount_threshold', '{"threshold": 500.0}', true),
    ('repeated_transaction', 'Repeated Transaction', 'Flag if same transaction repeats 3+ times in 10 minutes', 'repeated_transaction', '{"max_repeats": 3, "time_window_minutes": 10}', true),
    ('high_frequency', 'High Frequency', 'Flag if user makes 5+ transactions in 5 minutes', 'high_frequency', '{"max_transactions": 5, "time_window_minutes": 5}', true),
    ('large_percentage', 'Large Percentage', 'Flag if transaction exceeds 50% of user balance', 'large_percentage', '{"percentage_threshold": 50.0}', true)
ON CONFLICT (rule_id) DO NOTHING;


