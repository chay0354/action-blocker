"""
Standalone Action Blocker Service
Runs independently and monitors transactions in real-time
"""
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import threading
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))
from rules_engine import RulesEngine

# Load .env files - prioritize local .env, then fallback to wallet-back/.env
# First, try to load from action-blocker/.env (current directory)
local_env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(local_env_path):
    load_dotenv(local_env_path, override=True)  # override=True ensures local values take precedence
    print(f"✅ Loaded environment from: {local_env_path}")

# Also load from wallet-back/.env if it exists (for backward compatibility)
wallet_back_env_path = os.path.join(os.path.dirname(__file__), '..', 'wallet-back', '.env')
if os.path.exists(wallet_back_env_path):
    load_dotenv(wallet_back_env_path)  # This won't override existing values
    print(f"✅ Also loaded from: {wallet_back_env_path}")

# Final fallback to current directory .env (if not already loaded)
if not os.path.exists(local_env_path):
    load_dotenv()

class ActionBlockerHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for Action Blocker Service API"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/status' or self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            service = self.server.service
            status = service.get_status() if service else {"running": False}
            response = json.dumps({
                "status": "running" if status.get("running") else "stopped",
                **status
            })
            self.wfile.write(response.encode())
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/stop' or self.path == '/api/stop':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            service = self.server.service
            if service:
                service.stop()
                response = json.dumps({"message": "Service stopped", "status": "stopped"})
            else:
                response = json.dumps({"message": "Service not running", "status": "stopped"})
            self.wfile.write(response.encode())
        elif self.path == '/api/check-transaction' or self.path == '/check-transaction':
            # Check transaction endpoint
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                transaction_data = json.loads(post_data.decode('utf-8'))
                service = self.server.service
                
                if not service or not service.rules_engine:
                    self.send_response(503)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "Service not initialized",
                        "needs_approval": True,
                        "violations": ["Action Blocker Service is not running"]
                    }).encode())
                    return
                
                # Check transaction against rules
                context = {
                    "sender_balance": transaction_data.get("sender_balance", 0),
                    "supabase": service.supabase
                }
                
                transaction = {
                    "from_user_id": transaction_data.get("from_user_id"),
                    "to_user_id": transaction_data.get("to_user_id"),
                    "amount": transaction_data.get("amount")
                }
                
                needs_approval, violations = service.rules_engine.check_transaction(transaction, context)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = json.dumps({
                    "needs_approval": needs_approval,
                    "violations": violations,
                    "approved": not needs_approval
                })
                self.wfile.write(response.encode())
                
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e), "needs_approval": True}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logs"""
        pass


class ActionBlockerService:
    """Standalone service that monitors and blocks suspicious transactions"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        self.running = False
        self.thread = None
        self.http_thread = None
        self.http_server = None
        self.host = host
        self.port = port
        self.supabase: Optional[Client] = None
        self.rules_engine: Optional[RulesEngine] = None
        self.poll_interval = 2  # Check every 2 seconds
        self.last_checked_id = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down Action Blocker Service...")
        self.stop()
        sys.exit(0)
    
    def initialize(self):
        """Initialize Supabase connection and rules engine"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url:
                raise ValueError("SUPABASE_URL must be set in .env file (action-blocker/.env or wallet-back/.env)")
            if not supabase_service_key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY must be set in .env file (action-blocker/.env or wallet-back/.env)")
            
            print(f"🔗 Connecting to Supabase: {supabase_url[:30]}...")
            self.supabase = create_client(supabase_url, supabase_service_key)
            self.rules_engine = RulesEngine(self.supabase)
            
            print("✅ Action Blocker Service initialized")
            print(f"   Loaded {len(self.rules_engine.rules)} rules")
            for rule in self.rules_engine.rules:
                status = "🟢 Active" if rule.enabled else "🔴 Disabled"
                print(f"   - {rule.name}: {status}")
            
            return True
        except Exception as e:
            print(f"❌ Error initializing service: {e}")
            print(f"   Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in action-blocker/.env")
            return False
    
    def check_pending_transactions(self):
        """Check for new transactions that need to be reviewed"""
        try:
            # Get the latest transaction ID we've checked
            # We'll monitor the transactions table for new entries
            query = self.supabase.table("transactions").select("*").order("created_at", desc=True).limit(1)
            
            if self.last_checked_id:
                # Only get transactions newer than last checked
                query = query.gt("id", self.last_checked_id)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                # Process new transactions
                for tx in result.data:
                    self._process_transaction(tx)
                    self.last_checked_id = tx["id"]
        except Exception as e:
            print(f"⚠️  Error checking transactions: {e}")
    
    def _process_transaction(self, transaction: Dict[str, Any]):
        """Process a transaction and check if it should have been blocked"""
        try:
            # This is a post-processing check - transactions that already went through
            # We'll also monitor for new transfer attempts via a different method
            pass
        except Exception as e:
            print(f"⚠️  Error processing transaction: {e}")
    
    def monitor_transfer_requests(self):
        """Monitor for new transfer requests and check them before execution"""
        try:
            # Check for new pending transactions that were just created
            # These are transactions that were flagged by the backend
            pending_result = self.supabase.table("pending_transactions").select("*").eq(
                "status", "pending"
            ).order("created_at", desc=True).limit(10).execute()
            
            if pending_result.data:
                for pending_tx in pending_result.data:
                    # Log that we detected a flagged transaction
                    violations = pending_tx.get("violations", [])
                    if isinstance(violations, str):
                        violations = json.loads(violations)
                    
                    print(f"🚨 Flagged transaction detected:")
                    print(f"   From: {pending_tx.get('from_user_id')}")
                    print(f"   To: {pending_tx.get('to_user_id')}")
                    print(f"   Amount: ${pending_tx.get('amount')}")
                    print(f"   Violations: {len(violations)}")
                    for violation in violations:
                        print(f"      - {violation}")
        except Exception as e:
            print(f"⚠️  Error monitoring transfer requests: {e}")
    
    def start_http_server(self):
        """Start HTTP server for API endpoints"""
        try:
            server_address = (self.host, self.port)
            self.http_server = HTTPServer(server_address, ActionBlockerHTTPHandler)
            self.http_server.service = self  # Attach service instance
            
            def run_server():
                self.http_server.serve_forever()
            
            self.http_thread = threading.Thread(target=run_server, daemon=True)
            self.http_thread.start()
            print(f"🌐 HTTP API server running on http://{self.host}:{self.port}")
            print(f"   Status endpoint: http://{self.host}:{self.port}/api/status")
        except Exception as e:
            print(f"⚠️  Failed to start HTTP server: {e}")
    
    def run_loop(self):
        """Main service loop"""
        print("🔄 Action Blocker Service is running and monitoring transactions...")
        print("   Press Ctrl+C to stop\n")
        
        while self.running:
            try:
                # Reload rules periodically (in case they were updated)
                if self.rules_engine:
                    self.rules_engine.reload_rules()
                
                # Monitor for flagged transactions
                self.monitor_transfer_requests()
                
                # Check for new transactions
                self.check_pending_transactions()
                
                # Sleep before next check
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"⚠️  Error in service loop: {e}")
                time.sleep(self.poll_interval)
    
    def start(self):
        """Start the service"""
        if self.running:
            print("⚠️  Service is already running")
            return False
        
        if not self.initialize():
            return False
        
        # Start HTTP server
        self.start_http_server()
        
        self.running = True
        self.thread = threading.Thread(target=self.run_loop, daemon=True)
        self.thread.start()
        
        print("✅ Action Blocker Service started successfully")
        print(f"📍 Service URL: http://{self.host}:{self.port}")
        print(f"   Add this to wallet-back/.env: ACTION_BLOCKER_URL=http://{self.host}:{self.port}")
        return True
    
    def stop(self):
        """Stop the service"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop HTTP server
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
        
        if self.thread:
            self.thread.join(timeout=5)
        
        print("✅ Action Blocker Service stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "running": self.running,
            "rules_count": len(self.rules_engine.rules) if self.rules_engine else 0,
            "active_rules": sum(1 for r in self.rules_engine.rules if r.enabled) if self.rules_engine else 0,
            "poll_interval": self.poll_interval
        }


# Global service instance
_service_instance: Optional[ActionBlockerService] = None


def get_service() -> ActionBlockerService:
    """Get or create the global service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ActionBlockerService()
    return _service_instance


if __name__ == "__main__":
    """Run as standalone service"""
    print("=" * 60)
    print("🚀 Starting Action Blocker Service")
    print("=" * 60)
    
    # Get host and port from environment or use defaults
    host = os.getenv("ACTION_BLOCKER_HOST", "127.0.0.1")
    port = int(os.getenv("ACTION_BLOCKER_PORT", "8001"))
    
    service = ActionBlockerService(host=host, port=port)
    
    if not service.start():
        print("❌ Failed to start service")
        sys.exit(1)
    
    try:
        # Keep the main thread alive
        while service.running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal")
        service.stop()
        sys.exit(0)

