"""
Agent Integration Testing Module

This module tests the complete banking agent end-to-end functionality,
including tool integration, conversation flow, and user experience.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from ..agents.banking_agent import BankingAgent
from .conftest import (
    validate_json_response,
    SAMPLE_TEST_MESSAGES,
    TestCategories
)


class TestAgentBasicFunctionality:
    """Test basic agent functionality and responses."""
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test that agent initializes properly."""
        agent = BankingAgent()
        
        assert agent is not None, "Agent should initialize successfully"
        assert hasattr(agent, 'tools'), "Agent should have tools attribute"
        assert hasattr(agent, 'user_agents'), "Agent should have user_agents cache"
        assert len(agent.tools) > 0, "Agent should have at least one tool"
        
        # Test user-specific agent creation
        test_user_id = "test_user"
        user_agent = agent._get_user_agent(test_user_id)
        assert user_agent is not None, "Should create user-specific agent"
        assert test_user_id in agent.user_agents, "Should cache user-specific agent"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_basic_account_balance_request(self, banking_agent, test_user_data, test_thread_id):
        """Test basic account balance request."""
        user_id = test_user_data["user"].user_id
        message = "What's my account balance?"
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should return a result"
        assert "response" in result, "Result should contain response"
        assert "tools_used" in result, "Result should contain tools_used"
        assert "get_account_balance" in result["tools_used"], "Should use account balance tool"
        
        # Response should contain balance information
        response_text = result["response"].lower()
        assert any(word in response_text for word in ["balance", "account", "$", "usd"]), \
            "Response should contain balance-related information"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_basic_transaction_request(self, banking_agent, test_user_data, test_thread_id):
        """Test basic transaction history request."""
        user_id = test_user_data["user"].user_id
        message = "Show me my recent transactions"
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should return a result"
        assert "response" in result, "Result should contain response"
        assert "get_transactions" in result["tools_used"], "Should use transactions tool"
        
        response_text = result["response"].lower()
        assert any(word in response_text for word in ["transaction", "recent", "$", "debit", "credit"]), \
            "Response should contain transaction-related information"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_basic_credit_card_request(self, banking_agent, test_user_data, test_thread_id):
        """Test basic credit card information request."""
        user_id = test_user_data["user"].user_id
        message = "What's my credit card information?"
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should return a result"
        assert "response" in result, "Result should contain response"
        assert "get_credit_card_info" in result["tools_used"], "Should use credit card tool"
        
        response_text = result["response"].lower()
        assert any(word in response_text for word in ["card", "credit", "limit", "$"]), \
            "Response should contain credit card-related information"


class TestAgentConversationFlow:
    """Test agent conversation flow and context management."""
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, banking_agent, test_user_data, test_thread_id):
        """Test multi-turn conversation with context preservation."""
        user_id = test_user_data["user"].user_id
        
        # First message
        result1 = await banking_agent.chat(
            message="What's my account balance?",
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert "get_account_balance" in result1["tools_used"], "First message should use balance tool"
        
        # Second message in same thread
        result2 = await banking_agent.chat(
            message="Now show me my recent transactions",
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert "get_transactions" in result2["tools_used"], "Second message should use transactions tool"
        
        # Both results should have same thread_id
        assert result1["chat_thread_id"] == result2["chat_thread_id"], "Should maintain thread continuity"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_multiple_requests_in_one_message(self, banking_agent, test_user_data, test_thread_id):
        """Test handling multiple requests in a single message."""
        user_id = test_user_data["user"].user_id
        message = "Give me my balance of all accounts, my user id, and my email?"
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should handle multiple requests"
        assert "response" in result, "Result should contain response"
        
        # Should use account balance tool at minimum
        assert "get_account_balance" in result["tools_used"], "Should use account balance tool"
        
        response_text = result["response"].lower()
        # Should address the security concern about user_id and email
        # The agent should NOT provide user_id for security reasons
        assert ("security" in response_text or "cannot provide" in response_text), \
            "Response should explain security policy when asked for sensitive info"


class TestAgentErrorHandling:
    """Test agent error handling and recovery."""
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_invalid_user_handling(self, banking_agent, test_thread_id):
        """Test agent behavior with invalid user."""
        invalid_user_id = "nonexistent_user_12345"
        message = "What's my account balance?"
        
        result = await banking_agent.chat(
            message=message,
            user_id=invalid_user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should handle invalid user gracefully"
        assert "response" in result, "Should provide response even for invalid user"
        
        response_text = result["response"].lower()
        # Should indicate some kind of issue or inability to find information
        assert any(word in response_text for word in ["unable", "not found", "error", "issue", "sorry"]), \
            "Response should indicate inability to process request"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_ambiguous_request_handling(self, banking_agent, test_user_data, test_thread_id):
        """Test agent behavior with ambiguous requests."""
        user_id = test_user_data["user"].user_id
        message = "Tell me about my stuff"  # Ambiguous request
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Agent should handle ambiguous requests"
        assert "response" in result, "Should provide response"
        
        # Agent should either ask for clarification or provide general information
        response_text = result["response"].lower()
        assert len(response_text) > 20, "Should provide meaningful response to ambiguous request"
    
    @pytest.mark.agent
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_no_infinite_loops(self, banking_agent, test_user_data, test_thread_id):
        """Test that agent doesn't get stuck in infinite loops."""
        user_id = test_user_data["user"].user_id
        message = "What's my account balance?"
        
        start_time = datetime.now()
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (30 seconds max due to timeout)
        assert response_time < 30, f"Agent took {response_time:.2f}s, might be stuck in loop"
        assert result is not None, "Agent should return result within timeout"
        
        # Check for signs of infinite loops in response
        if "tools_used" in result:
            tool_counts = {}
            for tool in result["tools_used"]:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            
            # No tool should be called excessively
            for tool, count in tool_counts.items():
                assert count <= 5, f"Tool {tool} called {count} times, possible infinite loop"


class TestAgentPerformance:
    """Test agent performance characteristics."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_response_times(self, banking_agent, test_user_data, test_thread_id):
        """Test agent response times for various requests."""
        user_id = test_user_data["user"].user_id
        
        test_messages = [
            "What's my account balance?",
            "Show me my recent transactions",
            "What's my credit card information?"
        ]
        
        max_response_time = 10.0  # 10 seconds max per request
        
        for message in test_messages:
            start_time = datetime.now()
            
            result = await banking_agent.chat(
                message=message,
                user_id=user_id,
                chat_thread_id=f"{test_thread_id}_{message[:10]}"
            )
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            assert response_time < max_response_time, \
                f"Message '{message}' took {response_time:.2f}s, expected < {max_response_time}s"
            assert result is not None, f"Should get result for message '{message}'"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, banking_agent, test_user_data):
        """Test agent handling of concurrent requests."""
        user_id = test_user_data["user"].user_id
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(3):
            task = banking_agent.chat(
                message="What's my account balance?",
                user_id=user_id,
                chat_thread_id=f"concurrent_test_{i}"
            )
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should complete successfully
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Request {i} failed with exception: {result}"
            assert result is not None, f"Request {i} should return result"
            assert "response" in result, f"Request {i} should have response"


class TestAgentToolIntegration:
    """Test agent integration with all available tools."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_all_tools_accessible(self, banking_agent, test_user_data, test_thread_id):
        """Test that agent can access and use all available tools."""
        user_id = test_user_data["user"].user_id
        
        # Test messages that should trigger each tool
        tool_test_cases = [
            ("What's my account balance?", "get_account_balance"),
            ("Show me my transactions", "get_transactions"),
            ("What's my credit card info?", "get_credit_card_info"),
            # Note: search_bank_documents would need policy-related question
        ]
        
        for message, expected_tool in tool_test_cases:
            result = await banking_agent.chat(
                message=message,
                user_id=user_id,
                chat_thread_id=f"{test_thread_id}_{expected_tool}"
            )
            
            assert result is not None, f"Should get result for tool {expected_tool}"
            assert "tools_used" in result, f"Should track tools used for {expected_tool}"
            assert expected_tool in result["tools_used"], \
                f"Should use {expected_tool} for message '{message}'"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_parameter_passing(self, banking_agent, test_user_data, test_thread_id):
        """Test that agent passes correct parameters to tools."""
        user_id = test_user_data["user"].user_id
        
        # Request that should pass specific parameters
        message = "Show me my last 5 transactions from my checking account"
        
        result = await banking_agent.chat(
            message=message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Should get result"
        assert "get_transactions" in result["tools_used"], "Should use transactions tool"
        
        # The agent should have used the authenticated user_id
        # We can't directly inspect the tool parameters, but we can verify
        # the request completed successfully (no parameter validation errors)
        response_text = result["response"].lower()
        assert "error" not in response_text or "invalid" not in response_text, \
            "Should not have parameter validation errors"


class TestAgentRobustness:
    """Test agent robustness and edge cases."""
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_empty_message_handling(self, banking_agent, test_user_data, test_thread_id):
        """Test agent behavior with empty or very short messages."""
        user_id = test_user_data["user"].user_id
        
        empty_messages = ["", " ", "hi", "help"]
        
        for message in empty_messages:
            result = await banking_agent.chat(
                message=message,
                user_id=user_id,
                chat_thread_id=f"{test_thread_id}_{len(message)}"
            )
            
            assert result is not None, f"Should handle empty/short message: '{message}'"
            assert "response" in result, f"Should provide response for: '{message}'"
            
            # Should provide helpful response
            response_text = result["response"]
            assert len(response_text) > 10, f"Should provide meaningful response to '{message}'"
    
    @pytest.mark.agent
    @pytest.mark.asyncio
    async def test_very_long_message_handling(self, banking_agent, test_user_data, test_thread_id):
        """Test agent behavior with very long messages."""
        user_id = test_user_data["user"].user_id
        
        # Create a very long message
        long_message = "I want to know about my account balance. " * 50 + "What's my balance?"
        
        result = await banking_agent.chat(
            message=long_message,
            user_id=user_id,
            chat_thread_id=test_thread_id
        )
        
        assert result is not None, "Should handle very long messages"
        assert "response" in result, "Should provide response"
        
        # Should still understand the core request
        assert "get_account_balance" in result.get("tools_used", []), \
            "Should understand balance request in long message"


if __name__ == "__main__":
    # Run agent integration tests
    pytest.main([__file__, "-v", "--tb=short", "-m", "agent"])
