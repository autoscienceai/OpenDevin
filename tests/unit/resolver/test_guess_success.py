import json
from unittest.mock import MagicMock, patch

from openhands.core.config import LLMConfig
from openhands.events.action.message import MessageAction
from openhands.llm import LLM
from openhands.resolver.github_issue import GithubIssue
from openhands.resolver.issue_definitions import IssueHandler, PRHandler


def test_guess_success_multiline_explanation():
    # Mock data
    issue = GithubIssue(
        owner='test',
        repo='test',
        number=1,
        title='Test Issue',
        body='Test body',
        thread_comments=None,
        review_comments=None,
    )
    history = [MessageAction(content='Test message')]
    llm_config = LLMConfig(model='test', api_key='test')

    # Create a mock response with multi-line explanation
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The PR successfully addressed the issue by:
- Fixed bug A
- Added test B
- Updated documentation C

Automatic fix generated by OpenHands 🙌"""
            )
        )
    ]

    # Use patch to mock the LLM completion call
    with patch.object(LLM, 'completion', return_value=mock_response) as mock_completion:
        # Create a handler instance
        handler = IssueHandler('test', 'test', 'test', llm_config)

        # Call guess_success
        success, _, explanation = handler.guess_success(issue, history)

        # Verify the results
        assert success is True
        assert 'The PR successfully addressed the issue by:' in explanation
        assert 'Fixed bug A' in explanation
        assert 'Added test B' in explanation
        assert 'Updated documentation C' in explanation
        assert 'Automatic fix generated by OpenHands' in explanation

        # Verify that LLM completion was called exactly once
        mock_completion.assert_called_once()


def test_pr_handler_guess_success_with_thread_comments():
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Create a mock issue with thread comments but no review comments
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=['First comment', 'Second comment'],
        closing_issues=['Issue description'],
        review_comments=None,
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history
    history = [MessageAction(content='Fixed the issue by implementing X and Y')]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the feedback."""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion', return_value=mock_response):
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the results
        assert success is True
        assert success_list == [True]
        assert 'successfully address' in explanation
        assert len(json.loads(explanation)) == 1


def test_pr_handler_guess_success_only_review_comments():
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Create a mock issue with only review comments
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=None,
        closing_issues=['Issue description'],
        review_comments=['Please fix the formatting', 'Add more tests'],
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history
    history = [MessageAction(content='Fixed the formatting and added more tests')]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Mock the LLM response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content="""--- success
true

--- explanation
The changes successfully address the review comments."""
            )
        )
    ]

    # Test the guess_success method
    with patch.object(LLM, 'completion', return_value=mock_response):
        success, success_list, explanation = handler.guess_success(issue, history)

        # Verify the results
        assert success is True
        assert success_list == [True]
        assert (
            '["The changes successfully address the review comments."]' in explanation
        )


def test_pr_handler_guess_success_no_comments():
    # Create a PR handler instance
    llm_config = LLMConfig(model='test', api_key='test')
    handler = PRHandler('test-owner', 'test-repo', 'test-token', llm_config)

    # Create a mock issue with no comments
    issue = GithubIssue(
        owner='test-owner',
        repo='test-repo',
        number=1,
        title='Test PR',
        body='Test Body',
        thread_comments=None,
        closing_issues=['Issue description'],
        review_comments=None,
        thread_ids=None,
        head_branch='test-branch',
    )

    # Create mock history
    history = [MessageAction(content='Fixed the issue')]

    # Create mock LLM config
    llm_config = LLMConfig(model='test-model', api_key='test-key')

    # Test that it returns appropriate message when no comments are present
    success, success_list, explanation = handler.guess_success(issue, history)
    assert success is False
    assert success_list is None
    assert explanation == 'No feedback was found to process'