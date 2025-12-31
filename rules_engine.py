"""
Transaction Rules Engine
Checks transactions against defined rules and flags suspicious ones
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from supabase import Client


class Rule:
    """Base class for transaction rules"""
    def __init__(self, rule_id: str, name: str, description: str, enabled: bool = True):
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.enabled = enabled
    
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        """
        Check if transaction violates this rule
        Returns: (is_violated, reason)
        """
        raise NotImplementedError


class AmountThresholdRule(Rule):
    """Rule: Flag transactions above a certain amount"""
    def __init__(self, threshold: float, rule_id: str = "amount_threshold", **kwargs):
        super().__init__(rule_id, "Amount Threshold", f"Flag transactions above ${threshold}", **kwargs)
        self.threshold = threshold
    
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        if not self.enabled:
            return False, ""
        
        amount = float(transaction.get("amount", 0))
        if amount > self.threshold:
            return True, f"Transaction amount ${amount} exceeds threshold of ${self.threshold}"
        return False, ""


class RepeatedTransactionRule(Rule):
    """Rule: Flag if same transaction repeats multiple times within time window"""
    def __init__(self, max_repeats: int, time_window_minutes: int, rule_id: str = "repeated_transaction", **kwargs):
        super().__init__(
            rule_id, 
            "Repeated Transaction", 
            f"Flag if same transaction repeats {max_repeats} times within {time_window_minutes} minutes",
            **kwargs
        )
        self.max_repeats = max_repeats
        self.time_window_minutes = time_window_minutes
    
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        if not self.enabled:
            return False, ""
        
        supabase: Client = context.get("supabase")
        from_user_id = transaction.get("from_user_id")
        to_user_id = transaction.get("to_user_id")
        amount = transaction.get("amount")
        
        if not supabase or not from_user_id:
            return False, ""
        
        # Check recent transactions in the time window
        time_threshold = datetime.utcnow() - timedelta(minutes=self.time_window_minutes)
        
        try:
            recent_tx = supabase.table("transactions").select("*").eq(
                "from_user_id", from_user_id
            ).eq("to_user_id", to_user_id).eq("amount", amount).gte(
                "created_at", time_threshold.isoformat()
            ).execute()
            
            # Count includes the current transaction
            count = len(recent_tx.data) if recent_tx.data else 0
            
            if count >= self.max_repeats:
                return True, f"Same transaction repeated {count} times within {self.time_window_minutes} minutes"
        except Exception as e:
            print(f"Error checking repeated transaction rule: {e}")
        
        return False, ""


class HighFrequencyRule(Rule):
    """Rule: Flag if user makes too many transactions in a short time"""
    def __init__(self, max_transactions: int, time_window_minutes: int, rule_id: str = "high_frequency", **kwargs):
        super().__init__(
            rule_id,
            "High Frequency",
            f"Flag if user makes more than {max_transactions} transactions within {time_window_minutes} minutes",
            **kwargs
        )
        self.max_transactions = max_transactions
        self.time_window_minutes = time_window_minutes
    
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        if not self.enabled:
            return False, ""
        
        supabase: Client = context.get("supabase")
        from_user_id = transaction.get("from_user_id")
        
        if not supabase or not from_user_id:
            return False, ""
        
        time_threshold = datetime.utcnow() - timedelta(minutes=self.time_window_minutes)
        
        try:
            recent_tx = supabase.table("transactions").select("*").eq(
                "from_user_id", from_user_id
            ).gte("created_at", time_threshold.isoformat()).execute()
            
            count = len(recent_tx.data) if recent_tx.data else 0
            
            if count >= self.max_transactions:
                return True, f"User made {count} transactions within {self.time_window_minutes} minutes"
        except Exception as e:
            print(f"Error checking high frequency rule: {e}")
        
        return False, ""


class LargePercentageRule(Rule):
    """Rule: Flag if transaction is a large percentage of user's balance"""
    def __init__(self, percentage_threshold: float, rule_id: str = "large_percentage", **kwargs):
        super().__init__(
            rule_id,
            "Large Percentage",
            f"Flag if transaction exceeds {percentage_threshold}% of user's balance",
            **kwargs
        )
        self.percentage_threshold = percentage_threshold
    
    def check(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        if not self.enabled:
            return False, ""
        
        amount = float(transaction.get("amount", 0))
        user_balance = context.get("sender_balance", 0)
        
        if user_balance <= 0:
            return False, ""
        
        percentage = (amount / user_balance) * 100
        
        if percentage > self.percentage_threshold:
            return True, f"Transaction ${amount} is {percentage:.2f}% of balance ${user_balance} (threshold: {self.percentage_threshold}%)"
        
        return False, ""


class RulesEngine:
    """Main rules engine that checks transactions against all rules"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.rules: List[Rule] = []
        self._load_rules_from_db()
    
    def _load_rules_from_db(self):
        """Load rules from database, fallback to defaults if DB is empty"""
        try:
            # Try to load rules from database
            rules_result = self.supabase.table("transaction_rules").select("*").execute()
            
            if rules_result.data and len(rules_result.data) > 0:
                # Load rules from database
                self.rules = []
                for rule_data in rules_result.data:
                    rule = self._create_rule_from_db(rule_data)
                    if rule:
                        self.rules.append(rule)
                print(f"Loaded {len(self.rules)} rules from database")
            else:
                # Database is empty, load defaults
                print("No rules in database, loading defaults...")
                self._load_default_rules()
                # Save defaults to database
                self._save_defaults_to_db()
        except Exception as e:
            print(f"Error loading rules from database: {e}")
            # Fallback to defaults if database table doesn't exist
            print("Falling back to default rules...")
            self._load_default_rules()
    
    def _create_rule_from_db(self, rule_data: Dict[str, Any]) -> Optional[Rule]:
        """Create a rule instance from database data"""
        try:
            rule_type = rule_data.get("rule_type")
            rule_config = rule_data.get("rule_config", {})
            rule_id = rule_data.get("rule_id")
            enabled = rule_data.get("enabled", True)
            
            if rule_type == "amount_threshold":
                threshold = float(rule_config.get("threshold", 500.0))
                return AmountThresholdRule(threshold=threshold, rule_id=rule_id, enabled=enabled)
            
            elif rule_type == "repeated_transaction":
                max_repeats = int(rule_config.get("max_repeats", 3))
                time_window = int(rule_config.get("time_window_minutes", 10))
                return RepeatedTransactionRule(
                    max_repeats=max_repeats,
                    time_window_minutes=time_window,
                    rule_id=rule_id,
                    enabled=enabled
                )
            
            elif rule_type == "high_frequency":
                max_tx = int(rule_config.get("max_transactions", 5))
                time_window = int(rule_config.get("time_window_minutes", 5))
                return HighFrequencyRule(
                    max_transactions=max_tx,
                    time_window_minutes=time_window,
                    rule_id=rule_id,
                    enabled=enabled
                )
            
            elif rule_type == "large_percentage":
                percentage = float(rule_config.get("percentage_threshold", 50.0))
                return LargePercentageRule(
                    percentage_threshold=percentage,
                    rule_id=rule_id,
                    enabled=enabled
                )
        except Exception as e:
            print(f"Error creating rule from DB data: {e}")
        
        return None
    
    def _load_default_rules(self):
        """Load default rules (fallback)"""
        self.rules = []
        # Amount threshold: Flag transactions above $500
        self.rules.append(AmountThresholdRule(threshold=500.0))
        
        # Repeated transaction: Flag if same transaction repeats 3+ times in 10 minutes
        self.rules.append(RepeatedTransactionRule(max_repeats=3, time_window_minutes=10))
        
        # High frequency: Flag if user makes 5+ transactions in 5 minutes
        self.rules.append(HighFrequencyRule(max_transactions=5, time_window_minutes=5))
        
        # Large percentage: Flag if transaction is more than 50% of balance
        self.rules.append(LargePercentageRule(percentage_threshold=50.0))
    
    def _save_defaults_to_db(self):
        """Save default rules to database"""
        try:
            default_rules = [
                {
                    "rule_id": "amount_threshold",
                    "name": "Amount Threshold",
                    "description": "Flag transactions above $500",
                    "rule_type": "amount_threshold",
                    "rule_config": {"threshold": 500.0},
                    "enabled": True
                },
                {
                    "rule_id": "repeated_transaction",
                    "name": "Repeated Transaction",
                    "description": "Flag if same transaction repeats 3+ times in 10 minutes",
                    "rule_type": "repeated_transaction",
                    "rule_config": {"max_repeats": 3, "time_window_minutes": 10},
                    "enabled": True
                },
                {
                    "rule_id": "high_frequency",
                    "name": "High Frequency",
                    "description": "Flag if user makes 5+ transactions in 5 minutes",
                    "rule_type": "high_frequency",
                    "rule_config": {"max_transactions": 5, "time_window_minutes": 5},
                    "enabled": True
                },
                {
                    "rule_id": "large_percentage",
                    "name": "Large Percentage",
                    "description": "Flag if transaction exceeds 50% of user balance",
                    "rule_type": "large_percentage",
                    "rule_config": {"percentage_threshold": 50.0},
                    "enabled": True
                }
            ]
            
            for rule_data in default_rules:
                try:
                    self.supabase.table("transaction_rules").upsert(
                        rule_data,
                        on_conflict="rule_id"
                    ).execute()
                except Exception as e:
                    print(f"Error saving rule {rule_data['rule_id']} to DB: {e}")
        except Exception as e:
            print(f"Error saving defaults to database: {e}")
    
    def reload_rules(self):
        """Reload rules from database"""
        self._load_rules_from_db()
    
    def add_rule(self, rule: Rule):
        """Add a custom rule"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_id: str):
        """Remove a rule by ID"""
        self.rules = [r for r in self.rules if r.rule_id != rule_id]
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all rules as dictionaries with full details"""
        rules_list = []
        for rule in self.rules:
            rule_dict = {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": rule.description,
                "enabled": rule.enabled
            }
            
            # Add rule-specific config
            if isinstance(rule, AmountThresholdRule):
                rule_dict["rule_type"] = "amount_threshold"
                rule_dict["config"] = {"threshold": rule.threshold}
            elif isinstance(rule, RepeatedTransactionRule):
                rule_dict["rule_type"] = "repeated_transaction"
                rule_dict["config"] = {
                    "max_repeats": rule.max_repeats,
                    "time_window_minutes": rule.time_window_minutes
                }
            elif isinstance(rule, HighFrequencyRule):
                rule_dict["rule_type"] = "high_frequency"
                rule_dict["config"] = {
                    "max_transactions": rule.max_transactions,
                    "time_window_minutes": rule.time_window_minutes
                }
            elif isinstance(rule, LargePercentageRule):
                rule_dict["rule_type"] = "large_percentage"
                rule_dict["config"] = {"percentage_threshold": rule.percentage_threshold}
            
            rules_list.append(rule_dict)
        
        return rules_list
    
    def check_transaction(self, transaction: Dict[str, Any], context: Dict[str, Any]):
        """
        Check transaction against all rules
        Returns: (needs_approval, list_of_violations)
        """
        context["supabase"] = self.supabase
        violations = []
        
        for rule in self.rules:
            if rule.enabled:
                is_violated, reason = rule.check(transaction, context)
                if is_violated:
                    violations.append(f"{rule.name}: {reason}")
        
        needs_approval = len(violations) > 0
        return needs_approval, violations

