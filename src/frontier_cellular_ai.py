"""
Frontier Cellular AI - Learning and Optimization System
=========================================================

A self-optimizing, self-improving AI system with natural language communication.
"""

import time
import math
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from .cellular_ai import CellularAI, CellRole, CellState
from .cell.cell import Cell, CellType
from .temporal.engine import TemporalEngine
from .hash.non_avalanche import non_avalanche_hash


class LearningMode(Enum):
    """Learning modes for cells."""
    EXPERIMENTAL = "experimental"      # Learn from new experiences
    REFLECTIVE = "reflective"          # Learn from past decisions
    ADAPTIVE = "adaptive"              # Learn from environment changes
    COLLABORATIVE = "collaborative"    # Learn from other cells


@dataclass
class LearningExperience:
    """A learning experience for a cell."""
    experience_id: str
    input_data: Any
    output_data: Any
    reward: float
    timestamp: float
    cell_id: str
    context: Dict[str, Any]
    success: bool


@dataclass
class OptimizationGoal:
    """Optimization goal for the system."""
    goal_id: str
    target_metric: str
    target_value: float
    current_value: float
    priority: int
    deadline: Optional[float] = None


@dataclass
class NaturalLanguageMessage:
    """Natural language message for communication."""
    message_id: str
    sender_id: str
    receiver_id: str
    text: str
    intent: str
    confidence: float
    timestamp: float
    context: Dict[str, Any]


class LearningEngine:
    """
    Engine for cell learning and optimization.
    
    Each cell can learn from experiences, optimize its parameters,
    and improve its capabilities over time.
    """
    
    def __init__(self, ai: CellularAI):
        self.ai = ai
        self.experiences: List[LearningExperience] = []
        self.optimization_goals: List[OptimizationGoal] = []
        self.learning_models: Dict[str, Dict] = {}
        self.performance_history: List[Dict] = []
        
    def learn_from_experience(self, experience: LearningExperience) -> float:
        """
        Learn from a single experience.
        
        Args:
            experience: The learning experience
            
        Returns:
            Learning improvement score
        """
        cell_id = experience.cell_id
        
        # Initialize learning model if not exists
        if cell_id not in self.learning_models:
            self.learning_models[cell_id] = {
                "total_experiences": 0,
                "success_rate": 0.0,
                "avg_reward": 0.0,
                "parameters": {},
                "capabilities": []
            }
        
        model = self.learning_models[cell_id]
        
        # Update statistics
        model["total_experiences"] += 1
        model["success_rate"] = (
            model["success_rate"] * (model["total_experiences"] - 1) + 
            (1.0 if experience.success else 0.0)
        ) / model["total_experiences"]
        
        # Update average reward
        model["avg_reward"] = (
            model["avg_reward"] * (model["total_experiences"] - 1) + 
            experience.reward
        ) / model["total_experiences"]
        
        # Learn from the experience
        improvement = self._learn_from_experience(cell_id, experience)
        
        # Store experience
        self.experiences.append(experience)
        
        return improvement
    
    def _learn_from_experience(self, cell_id: str, experience: LearningExperience) -> float:
        """Learn from a specific experience."""
        # Analyze the experience
        analysis = self._analyze_experience(experience)
        
        # Update cell parameters based on learning
        cell = self.ai._get_cell_by_id(cell_id)
        if cell:
            # Adjust temporal parameters for better precision
            self._optimize_temporal_parameters(cell, analysis)
            
            # Update cell capabilities
            self._update_capabilities(cell, analysis)
        
        return analysis["improvement_score"]
    
    def _analyze_experience(self, experience: LearningExperience) -> Dict:
        """Analyze an experience to extract learning."""
        # Calculate improvement score
        improvement_score = 0.0
        
        if experience.success:
            improvement_score = experience.reward * 0.1
        else:
            improvement_score = -experience.reward * 0.05
        
        # Extract patterns
        patterns = self._extract_patterns(experience)
        
        return {
            "improvement_score": improvement_score,
            "patterns": patterns,
            "success": experience.success,
            "reward": experience.reward,
            "timestamp": experience.timestamp
        }
    
    def _extract_patterns(self, experience: LearningExperience) -> List[str]:
        """Extract patterns from an experience."""
        patterns = []
        
        # Analyze input-output relationship
        input_type = type(experience.input_data).__name__
        output_type = type(experience.output_data).__name__
        
        patterns.append(f"{input_type}_to_{output_type}")
        
        # Analyze context
        if experience.context:
            for key in experience.context.keys():
                patterns.append(f"context_{key}")
        
        return patterns
    
    def _optimize_temporal_parameters(self, cell: Cell, analysis: Dict):
        """Optimize temporal parameters based on learning."""
        # Get cell's temporal engine
        engine = cell.get_temporal_engine()
        
        # Adjust echo depth based on performance
        if analysis["improvement_score"] > 0:
            # Increase echo depth for better precision
            engine.echo_depth = min(12, engine.echo_depth + 1)
        else:
            # Decrease echo depth for efficiency
            engine.echo_depth = max(4, engine.echo_depth - 1)
    
    def _update_capabilities(self, cell: Cell, analysis: Dict):
        """Update cell capabilities based on learning."""
        # Add new capabilities if successful
        if analysis["success"]:
            cell_type = cell.get_type()
            capability = f"capability_{cell_type.value}"
            
            # Get current capabilities
            shard = cell.get_shard()
            capability_section = shard.get_capability()
            
            if capability not in capability_section.differentiation_potential:
                capability_section.differentiation_potential.append(capability)
    
    def optimize_system(self) -> Dict:
        """
        Optimize the entire system.
        
        Returns:
            Optimization results
        """
        optimization_results = {
            "cells_optimized": 0,
            "goals_completed": 0,
            "performance_improvement": 0.0,
            "new_capabilities": []
        }
        
        # Optimize each cell
        for cell_id, role in self.ai.cell_roles.items():
            cell = self.ai._get_cell_by_id(cell_id)
            if cell and cell.is_alive():
                improvement = self._optimize_cell(cell)
                if improvement > 0:
                    optimization_results["cells_optimized"] += 1
                    optimization_results["performance_improvement"] += improvement
        
        # Check and complete optimization goals
        completed_goals = self._check_optimization_goals()
        optimization_results["goals_completed"] = len(completed_goals)
        
        # Add new capabilities
        new_capabilities = self._discover_new_capabilities()
        optimization_results["new_capabilities"] = new_capabilities
        
        return optimization_results
    
    def _optimize_cell(self, cell: Cell) -> float:
        """Optimize a single cell."""
        cell_id = cell.get_id()
        model = self.learning_models.get(cell_id, {})
        
        if not model:
            return 0.0
        
        # Calculate optimization potential
        success_rate = model.get("success_rate", 0.0)
        avg_reward = model.get("avg_reward", 0.0)
        
        # Optimize based on performance
        improvement = 0.0
        
        if success_rate > 0.8:
            # High success rate - optimize for precision
            improvement = 0.1 * success_rate
        elif success_rate > 0.5:
            # Medium success rate - optimize for stability
            improvement = 0.05 * success_rate
        else:
            # Low success rate - optimize for learning
            improvement = 0.02 * (1.0 - success_rate)
        
        return improvement
    
    def _check_optimization_goals(self) -> List[OptimizationGoal]:
        """Check and complete optimization goals."""
        completed = []
        
        for goal in self.optimization_goals:
            # Check if goal is completed
            if goal.target_metric == "temporal_precision":
                current = self.ai.get_temporal_analysis().get("avg_temporal_precision", 1.0)
                if current <= goal.target_value:
                    completed.append(goal)
            elif goal.target_metric == "confidence":
                # Check average confidence
                confidences = [d.confidence for d in self.ai.decision_history]
                if confidences and sum(confidences) / len(confidences) >= goal.target_value:
                    completed.append(goal)
        
        # Remove completed goals
        self.optimization_goals = [g for g in self.optimization_goals if g not in completed]
        
        return completed
    
    def _discover_new_capabilities(self) -> List[str]:
        """Discover new capabilities through optimization."""
        new_capabilities = []
        
        # Analyze performance patterns
        if len(self.experiences) > 10:
            # Find successful patterns
            successful = [e for e in self.experiences if e.success]
            if successful:
                # Extract common patterns
                patterns = set()
                for exp in successful:
                    for pattern in self._extract_patterns(exp):
                        patterns.add(pattern)
                
                # Add new capabilities based on patterns
                for pattern in list(patterns)[:5]:  # Limit to 5 new capabilities
                    new_capabilities.append(pattern)
        
        return new_capabilities
    
    def add_optimization_goal(self, goal: OptimizationGoal):
        """Add a new optimization goal."""
        self.optimization_goals.append(goal)


class NaturalLanguageInterface:
    """
    Natural language communication interface for the Cellular AI.
    
    Enables the system to understand and generate natural language
    messages for human interaction.
    """
    
    def __init__(self, ai: CellularAI):
        self.ai = ai
        self.message_history: List[NaturalLanguageMessage] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.vocabulary: Dict[str, List[str]] = {
            "greetings": ["hello", "hi", "hey", "good morning", "good afternoon"],
            "questions": ["what", "how", "why", "when", "where", "who"],
            "commands": ["run", "process", "analyze", "optimize", "learn", "create"],
            "status": ["status", "health", "performance", "capabilities"]
        }
    
    def process_message(self, text: str, sender_id: str = "user") -> Dict:
        """
        Process a natural language message.
        
        Args:
            text: The message text
            sender_id: The sender identifier
            
        Returns:
            Response dictionary
        """
        # Clean and normalize the text
        text = text.lower().strip()
        
        # Extract intent
        intent = self._extract_intent(text)
        
        # Generate response
        response = self._generate_response(intent, text, sender_id)
        
        # Store message
        message = NaturalLanguageMessage(
            message_id=f"msg_{len(self.message_history)}",
            sender_id=sender_id,
            receiver_id="ai",
            text=text,
            intent=intent,
            confidence=self._calculate_confidence(intent, text),
            timestamp=time.time(),
            context={"sender": sender_id}
        )
        self.message_history.append(message)
        
        return response
    
    def _extract_intent(self, text: str) -> str:
        """Extract intent from text."""
        # Check for status first (more specific)
        for status in self.vocabulary["status"]:
            if status in text:
                return "status"
        
        # Check for greetings
        for greeting in self.vocabulary["greetings"]:
            if greeting in text:
                return "greeting"
        
        # Check for questions
        for question in self.vocabulary["questions"]:
            if question in text:
                return "question"
        
        # Check for commands
        for command in self.vocabulary["commands"]:
            if command in text:
                return "command"
        
        # Default to general
        return "general"
    
    def _generate_response(self, intent: str, text: str, sender_id: str) -> Dict:
        """Generate a response based on intent."""
        if intent == "greeting":
            return {
                "response": "Hello! I am a Cellular AI system. How can I help you?",
                "intent": "greeting",
                "confidence": 0.95
            }
        elif intent == "question":
            return self._answer_question(text)
        elif intent == "command":
            return self._execute_command(text)
        elif intent == "status":
            return self._provide_status()
        else:
            return {
                "response": "I understand you want to communicate. Could you please clarify your request?",
                "intent": "general",
                "confidence": 0.8
            }
    
    def _answer_question(self, text: str) -> Dict:
        """Answer a question."""
        # Extract key terms
        terms = self._extract_terms(text)
        
        # Search knowledge base
        answer = self._search_knowledge_base(terms)
        
        if answer:
            return {
                "response": answer,
                "intent": "question",
                "confidence": 0.9
            }
        else:
            return {
                "response": "I don't have specific information about that yet. Would you like me to learn about it?",
                "intent": "question",
                "confidence": 0.7
            }
    
    def _execute_command(self, text: str) -> Dict:
        """Execute a command."""
        # Extract command type
        if "optimize" in text:
            result = self.ai.optimize()
            return {
                "response": f"System optimized. {result['cells_optimized']} cells optimized.",
                "intent": "command",
                "confidence": 0.95
            }
        elif "learn" in text:
            return {
                "response": "I am ready to learn. Please provide experiences for me to learn from.",
                "intent": "command",
                "confidence": 0.95
            }
        elif "create" in text:
            return {
                "response": "I can create new cells. What type of cell would you like me to create?",
                "intent": "command",
                "confidence": 0.95
            }
        else:
            return {
                "response": "Command received. Processing...",
                "intent": "command",
                "confidence": 0.8
            }
    
    def _provide_status(self) -> Dict:
        """Provide system status."""
        state = self.ai.get_system_state()
        temporal = self.ai.get_temporal_analysis()
        
        # Handle empty temporal analysis
        if not temporal:
            precision_str = "N/A"
        else:
            precision_str = f"{temporal['avg_temporal_precision'] * 1e12:.3f} ps"
        
        return {
            "response": f"System Status: {state['total_cells']} cells, "
                       f"{state['alive_cells']} alive, "
                       f"{state['total_decisions']} decisions, "
                       f"Precision: {precision_str}",
            "intent": "status",
            "confidence": 0.95
        }
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Simple term extraction
        words = text.split()
        # Remove common words and punctuation
        common_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "what", "how", "why", "when", "where", "who"}
        terms = []
        for word in words:
            # Strip punctuation
            word = word.strip("?.!,;:")
            if word and word.lower() not in common_words:
                terms.append(word.lower())
        return terms
    
    def _search_knowledge_base(self, terms: List[str]) -> Optional[str]:
        """Search knowledge base for terms."""
        for term in terms:
            if term in self.knowledge_base:
                return self.knowledge_base[term]
        return None
    
    def _calculate_confidence(self, intent: str, text: str) -> float:
        """Calculate confidence in intent classification."""
        # Base confidence
        confidence = 0.8
        
        # Increase confidence for clear patterns
        if intent in ["greeting", "command", "status"]:
            confidence = 0.95
        elif intent == "question":
            confidence = 0.9
        
        # Decrease confidence for ambiguous text
        if len(text.split()) < 3:
            confidence *= 0.8
        
        return confidence
    
    def add_to_knowledge_base(self, term: str, knowledge: Any):
        """Add knowledge to the knowledge base."""
        self.knowledge_base[term] = knowledge
    
    def get_message_history(self) -> List[Dict]:
        """Get message history."""
        return [
            {
                "message_id": m.message_id,
                "sender_id": m.sender_id,
                "text": m.text,
                "intent": m.intent,
                "confidence": m.confidence,
                "timestamp": m.timestamp
            }
            for m in self.message_history
        ]


class FrontierCellularAI(CellularAI):
    """
    Frontier Cellular AI with learning, optimization, and natural language.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        
        # Initialize learning engine
        self.learning_engine = LearningEngine(self)
        
        # Initialize natural language interface
        self.nli = NaturalLanguageInterface(self)
        
        # Add initial optimization goals
        self._add_initial_goals()
    
    def _add_initial_goals(self):
        """Add initial optimization goals."""
        self.learning_engine.add_optimization_goal(OptimizationGoal(
            goal_id="goal_1",
            target_metric="temporal_precision",
            target_value=1e-14,  # 0.01 ps
            current_value=1e-12,
            priority=1
        ))
    
    def learn(self, experience: LearningExperience):
        """Learn from an experience."""
        self.learning_engine.learn_from_experience(experience)
    
    def optimize(self) -> Dict:
        """Optimize the system."""
        return self.learning_engine.optimize_system()
    
    def communicate(self, text: str, sender_id: str = "user") -> Dict:
        """Communicate using natural language."""
        return self.nli.process_message(text, sender_id)
    
    def add_knowledge(self, term: str, knowledge: Any):
        """Add knowledge to the system."""
        self.nli.add_to_knowledge_base(term, knowledge)
    
    def get_communication_history(self) -> List[Dict]:
        """Get communication history."""
        return self.nli.get_message_history()
    
    def __repr__(self) -> str:
        state = self.get_system_state()
        temporal = self.get_temporal_analysis()
        return (
            f"FrontierCellularAI(cells={state['total_cells']}, alive={state['alive_cells']}, "
            f"decisions={state['total_decisions']}, precision={temporal.get('avg_temporal_precision', 0)*1e12:.3f}ps)"
        )


# Example usage
if __name__ == "__main__":
    # Create frontier cellular AI
    ai = FrontierCellularAI()
    
    # Communicate with the system
    response = ai.communicate("Hello!")
    print(f"🗣️  Response: {response['response']}")
    
    # Ask about status
    response = ai.communicate("What is your status?")
    print(f"📊 Status: {response['response']}")
    
    # Create cells
    ai.create_cell(CellRole.PERCEPTION)
    ai.create_cell(CellRole.REASONING)
    ai.create_cell(CellRole.MEMORY)
    ai.create_cell(CellRole.ACTION)
    
    # Process input
    input_data = {"type": "sensor", "value": 42}
    output = ai.think(input_data)
    
    # Learn from the experience
    from src.cellular_ai import CellRole
    experience = LearningExperience(
        experience_id="exp_1",
        input_data=input_data,
        output_data=output,
        reward=0.8,
        timestamp=time.time(),
        cell_id="supervisor",
        context={"type": "sensor"},
        success=True
    )
    ai.learn(experience)
    
    # Optimize the system
    optimization = ai.optimize()
    print(f"🔧 Optimization: {optimization}")
    
    # Communicate again
    response = ai.communicate("Optimize the system")
    print(f"🗣️  Response: {response['response']}")
    
    # Add knowledge
    ai.add_knowledge("cellular_ai", "A self-organizing AI system")
    response = ai.communicate("What is cellular AI?")
    print(f"📚 Knowledge: {response['response']}")
