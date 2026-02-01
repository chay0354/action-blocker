-- Create transaction_analyses table for Kernel decision layer
-- Stores each analysis with kernel_decision (null during runtime, final value on completion)
CREATE TABLE IF NOT EXISTS public.transaction_analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    from_user_id UUID NOT NULL,
    to_user_id UUID NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    violations JSONB,
    kernel_decision VARCHAR(1),  -- "N" (allow) | "L" (block) | null (during runtime)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transaction_analyses_created_at ON public.transaction_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transaction_analyses_from_user ON public.transaction_analyses(from_user_id);

ALTER TABLE public.transaction_analyses ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Service role full access" ON public.transaction_analyses;
CREATE POLICY "Service role full access" ON public.transaction_analyses FOR ALL USING (true);
