"""
State Machine for managing information states and decisions
States: K (Known), C (Checked), B (Blocked), N (New), L (Limited)
"""
import logging
from enum import Enum
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class State(Enum):
    """Information states"""
    K = "K"  # Known - Verified and approved
    C = "C"  # Checked - Under review
    B = "B"  # Blocked - Rejected/blocked
    N = "N"  # New - Initial state
    L = "L"  # Limited - Restricted access


class KernelDecision(Enum):
    """Kernel decision types"""
    ALLOW = "allow"
    BLOCK = "block"
    STOP = "stop"


class StateMachine:
    """State Machine for managing information states"""
    
    # Valid state transitions
    TRANSITIONS = {
        State.N: [State.C, State.K, State.B, State.L],  # New can go to any state
        State.C: [State.K, State.B, State.L],  # Checked can be approved, blocked, or limited
        State.K: [State.C, State.B, State.L],  # Known can be re-checked, blocked, or limited
        State.B: [State.C, State.N],  # Blocked can be re-checked or reset
        State.L: [State.C, State.K, State.B]  # Limited can be checked, approved, or blocked
    }
    
    def __init__(self, db: Optional[object] = None):
        """Initialize State Machine
        
        Args:
            db: Optional database session (not currently used, reserved for future audit logging)
        """
        self.db = db
    
    def get_state(self, query_id: str) -> Optional[State]:
        """Get current state for a query/decision"""
        # In a full implementation, this would query a state_history table
        # For now, return default state N (New)
        return State.N
    
    def can_transition(self, from_state: State, to_state: State) -> bool:
        """Check if transition is valid"""
        return to_state in self.TRANSITIONS.get(from_state, [])
    
    def transition(self, query_id: str, from_state: State, to_state: State, reason: str = "") -> bool:
        """Transition to new state and log the change"""
        if not self.can_transition(from_state, to_state):
            logger.warning(f"Invalid transition from {from_state.value} to {to_state.value}")
            return False
        
        # Log state transition
        logger.info(f"State transition: {query_id} {from_state.value} -> {to_state.value} ({reason})")
        
        # In a full implementation, this would:
        # 1. Save to state_history table
        # 2. Update current state
        # 3. Create audit log entry
        
        return True
    
    def log_state_change(self, query_id: str, state: State, decision: KernelDecision, reason: str = ""):
        """Log state change for audit trail"""
        # Handle both enum and string values
        state_val = state.value if hasattr(state, 'value') else str(state)
        decision_val = decision.value if hasattr(decision, 'value') else str(decision)
        logger.info(f"State change logged: {query_id} -> {state_val}, Decision: {decision_val}, Reason: {reason}")
        # In production, save to audit_log table


class Kernel:
    """
    Kernel - Supreme authority over all user responses
    Orchestrates: User Intent → Agents → Decision (Allow/Block/Stop)
    """
    
    def __init__(self, rag_service, state_machine: StateMachine):
        self.rag_service = rag_service
        self.state_machine = state_machine
    
    def process_user_intent(
        self,
        query: str,
        user_id: Optional[int] = None,
        context: Optional[str] = None,
        filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Process user intent through the Kernel system
        
        Flow: User Intent → Kernel → Agents → Kernel → Decision
        
        Args:
            query: User's question/intent
            user_id: Optional user ID for permissions
            context: Optional context from previous interactions
            
        Returns:
            Dictionary with decision, answer, state, and agent results
        """
        query_id = f"query_{datetime.utcnow().timestamp()}"
        initial_state = State.N  # Start with New state
        
        logger.info(f"Kernel processing user intent: {query_id}")
        
        # Step 1: Get initial answer from Doc Agent
        doc_agent_result = None
        doc_answer = None
        doc_context = None
        doc_search_results = []
        
        try:
            if context:
                # Use provided context
                doc_context = context
                # Generate answer from context
                if self.rag_service.llm_service.is_available():
                    doc_answer = self.rag_service.llm_service.generate_answer(query, doc_context)
            else:
                # Get answer from RAG (Doc Agent)
                doc_result = self.rag_service.generate_answer(query, n_results=5, filter_metadata=filter_metadata, use_llm=True)
                doc_answer = doc_result.get('answer')
                doc_context = doc_result.get('context', '')
                doc_search_results = doc_result.get('results', [])
                doc_agent_result = doc_result
            
            if not doc_answer:
                # No answer from Doc Agent - Stop
                self.state_machine.log_state_change(query_id, State.B, KernelDecision.STOP, "No answer from Doc Agent")
                return {
                    'decision': KernelDecision.STOP.value,
                    'state': State.B.value,
                    'answer': None,
                    'reason': 'לא נמצאה תשובה במסמכים',
                    'agent_results': {
                        'doc_agent': {'status': 'no_answer'}
                    }
                }
        except Exception as e:
            logger.error(f"Doc Agent error: {e}")
            self.state_machine.log_state_change(query_id, State.B, KernelDecision.STOP, f"Doc Agent error: {str(e)}")
            return {
                'decision': KernelDecision.STOP.value,
                'state': State.B.value,
                'answer': None,
                'reason': 'שגיאה בקבלת תשובה',
                'agent_results': {
                    'doc_agent': {'status': 'error', 'error': str(e)}
                }
            }
        
        # Step 2 & 3: Skip Contradiction and Risk Agents for now
        # (User requested to accept all answers and only run Doc Agent)
        contradiction_result = None
        has_contradictions = False
        risk_result = None
        has_risks = False
        
        # Step 4: Kernel Decision Logic - Always Allow for now
        decision = KernelDecision.ALLOW
        new_state = State.K  # Always set to Known (approved)
        reason = "תשובה מאושרת"
        self.state_machine.transition(query_id, initial_state, new_state, reason)
        
        # Log final decision
        self.state_machine.log_state_change(query_id, new_state, decision, reason)
        
        # Step 5: Return result
        result = {
            'decision': decision.value,
            'state': new_state.value,
            'answer': doc_answer,
            'reason': reason,
            'query_id': query_id,
            'context': doc_context,  # Include context for agent checks
            'search_results': doc_search_results,  # Include search results
            'agent_results': {
                'doc_agent': {
                    'status': 'success',
                    'answer': doc_answer,
                    'context_sources': doc_agent_result.get('context_used', 0) if doc_agent_result else 0,
                    'results_count': len(doc_search_results)
                },
                'contradiction_agent': {
                    'status': 'skipped',
                    'has_contradictions': False,
                    'analysis': None
                },
                'risk_agent': {
                    'status': 'skipped',
                    'has_risks': False,
                    'analysis': None
                }
            }
        }
        
        return result
