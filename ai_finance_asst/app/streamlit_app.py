import sys
import tempfile
from pathlib import Path

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage

# Ensure project root is on the path so we can import from agent/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from agent.finance_qa_agent import qa_executor
from agent.portfolio_agent import portfolio_executor
from agent.market_analysis_agent import market_executor
from agent.news_synthesizer_agent import news_executor


APP_TITLE = "AI Finance Assistant"

# Sample questions shown as clickable chips in each tab
SAMPLES = {
	"qa": [
		"What is asset allocation and why does it matter?",
		"Explain the benefits of dollar-cost averaging",
		"What are the tax advantages of retirement accounts?",
	],
	"portfolio": [
		"Summarize my top performers and overall return",
		"How diversified is my portfolio across sectors?",
		"What is my asset allocation and risk profile?",
	],
	"market": [
		"What is the current price and fundamentals of IBM?",
		"Show me IBM's daily price trend for the last 10 days",
		"What sector is IBM in and what are its key valuation metrics?",
	],
	"news": [
		"What are the latest financial market headlines?",
		"Summarize recent news about technology stocks",
		"What is the current market sentiment in the finance sector?",
	],
}

# Keys for per-tab chat history stored in session_state
HISTORY_KEYS = {
	"qa": "qa_history",
	"portfolio": "portfolio_history",
	"market": "market_history",
	"news": "news_history",
}


def _render_header():
	st.set_page_config(page_title=APP_TITLE, layout="wide")
	st.title(APP_TITLE)
	st.caption("Run specialized finance agents from a single interface.")


def _render_sidebar():
	"""Render the user profile panel in the sidebar."""
	with st.sidebar:
		st.header("User Profile")

		name = st.text_input(
			"Name",
			value=st.session_state.get("profile_name", ""),
			placeholder="Your name",
		)
		risk = st.selectbox(
			"Risk Tolerance",
			options=["", "Conservative", "Moderate", "Aggressive"],
			index=["", "Conservative", "Moderate", "Aggressive"].index(
				st.session_state.get("profile_risk", "")
			),
		)
		goals = st.text_area(
			"Investment Goals",
			value=st.session_state.get("profile_goals", ""),
			placeholder="e.g. Long-term growth, retirement in 20 years",
		)

		if st.button("Save Profile", type="primary"):
			st.session_state["profile_name"] = name
			st.session_state["profile_risk"] = risk
			st.session_state["profile_goals"] = goals
			st.success("Profile saved.")

		st.divider()

		if st.button("Clear All History", use_container_width=True):
			for key in HISTORY_KEYS.values():
				st.session_state[key] = []
			st.rerun()


def _build_input(user_input: str) -> str:
	"""Prepend profile context to the user's message if a profile is set."""
	parts = []
	if st.session_state.get("profile_name"):
		parts.append(f"User: {st.session_state['profile_name']}")
	if st.session_state.get("profile_risk"):
		parts.append(f"Risk Tolerance: {st.session_state['profile_risk']}")
	if st.session_state.get("profile_goals"):
		parts.append(f"Goals: {st.session_state['profile_goals']}")
	prefix = f"[{' | '.join(parts)}]\n\n" if parts else ""
	return prefix + user_input


def _run_agent(executor, user_input: str, history_key: str) -> str:
	"""Invoke the agent with conversation history and persist the exchange."""
	chat_history = []
	for h, a in st.session_state.get(history_key, []):
		chat_history.append(HumanMessage(content=h))
		chat_history.append(AIMessage(content=a))

	result = executor.invoke({"input": user_input, "chat_history": chat_history})
	output = result.get("output", "No output returned.")

	st.session_state[history_key].append((user_input, output))
	return output


def _render_chat_history(history_key: str):
	"""Display previous exchanges for this tab as chat bubbles."""
	for human_msg, ai_msg in st.session_state.get(history_key, []):
		with st.chat_message("user"):
			st.write(human_msg)
		with st.chat_message("assistant"):
			st.markdown(ai_msg)


def _sample_buttons(key_prefix: str, samples: list[str]):
	"""Render sample question buttons. Clicking one writes it to session_state."""
	st.caption("Try a sample question:")
	cols = st.columns(len(samples))
	for i, sample in enumerate(samples):
		with cols[i]:
			if st.button(sample, key=f"{key_prefix}_sample_{i}", use_container_width=True):
				st.session_state[key_prefix] = sample


def _render_finance_qa_tab():
	st.subheader("Finance Q&A")
	st.write("Ask questions grounded in your document knowledge base.")

	_render_chat_history("qa_history")

	_sample_buttons("qa", SAMPLES["qa"])

	question = st.text_area(
		"Question",
		value=st.session_state.get("qa", ""),
		placeholder="What are the key financial trends for 2024?",
	)
	if st.button("Run Finance Q&A", type="primary"):
		if not question.strip():
			st.warning("Please enter a question.")
			return
		with st.spinner("Running Finance Q&A agent..."):
			output = _run_agent(qa_executor, _build_input(question), "qa_history")
		with st.chat_message("user"):
			st.write(question)
		with st.chat_message("assistant"):
			st.markdown(output)


def _render_portfolio_tab():
	st.subheader("Portfolio Analysis")
	st.write("Analyze your portfolio for allocation, risk, and diversification insights.")

	_render_chat_history("portfolio_history")

	uploaded_file = st.file_uploader("Upload portfolio file (.xlsx)", type=["xlsx"])
	fallback_path = (Path(__file__).resolve().parent.parent / "tools" / "sample_portfolio.xlsx").as_posix()
	st.caption(f"If no file is uploaded, the default sample file is used: {fallback_path}")

	_sample_buttons("portfolio", SAMPLES["portfolio"])

	focus = st.text_area(
		"What would you like to know? (optional)",
		value=st.session_state.get("portfolio", ""),
		placeholder="Summarize my top performers and overall return",
	)

	if st.button("Run Portfolio Analysis", type="primary"):
		if uploaded_file is not None:
			with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
				tmp_file.write(uploaded_file.read())
				file_path = tmp_file.name
		else:
			file_path = fallback_path

		question_part = focus.strip() if focus.strip() else "give me insights"
		user_input = f"Analyze my portfolio from {file_path} and {question_part}."
		with st.spinner("Running Portfolio Analysis agent..."):
			output = _run_agent(portfolio_executor, _build_input(user_input), "portfolio_history")

		with st.chat_message("user"):
			st.write(user_input)
		with st.chat_message("assistant"):
			st.markdown(output)

		# Display charts directly from the analysis_output directory.
		output_dir = Path(__file__).resolve().parent.parent / "analysis_output"
		chart_files = sorted(output_dir.glob("*.png"))
		if chart_files:
			st.markdown("---")
			st.markdown("#### Portfolio Charts")
			col1, col2 = st.columns(2)
			for i, chart_path in enumerate(chart_files):
				caption = chart_path.stem.replace("_", " ").title()
				with (col1 if i % 2 == 0 else col2):
					st.image(str(chart_path), caption=caption, use_container_width=True)


def _render_market_tab():
	st.subheader("Market Analysis")
	st.write("Fetch live market data, quotes, and company fundamentals.")

	_render_chat_history("market_history")

	_sample_buttons("market", SAMPLES["market"])

	request = st.text_area(
		"Request",
		value=st.session_state.get("market", ""),
		placeholder="What's the current price of AAPL and its daily trend?",
	)
	if st.button("Run Market Analysis", type="primary"):
		if not request.strip():
			st.warning("Please enter a request.")
			return
		with st.spinner("Running Market Analysis agent..."):
			output = _run_agent(market_executor, _build_input(request), "market_history")
		with st.chat_message("user"):
			st.write(request)
		with st.chat_message("assistant"):
			st.markdown(output)


def _render_news_tab():
	st.subheader("News Synthesizer")
	st.write("Summarize market news, sentiment, and headlines.")

	_render_chat_history("news_history")

	_sample_buttons("news", SAMPLES["news"])

	request = st.text_area(
		"Request",
		value=st.session_state.get("news", ""),
		placeholder="Summarize the latest news about Apple stock.",
	)
	if st.button("Run News Synthesizer", type="primary"):
		if not request.strip():
			st.warning("Please enter a request.")
			return
		with st.spinner("Running News Synthesizer agent..."):
			output = _run_agent(news_executor, _build_input(request), "news_history")
		with st.chat_message("user"):
			st.write(request)
		with st.chat_message("assistant"):
			st.markdown(output)


def main():
	_render_header()

	# Initialise per-tab history lists once per session
	for key in HISTORY_KEYS.values():
		if key not in st.session_state:
			st.session_state[key] = []

	_render_sidebar()

	tabs = st.tabs([
		"Finance Q&A",
		"Portfolio Analysis",
		"Market Analysis",
		"News Synthesizer",
	])

	with tabs[0]:
		_render_finance_qa_tab()
	with tabs[1]:
		_render_portfolio_tab()
	with tabs[2]:
		_render_market_tab()
	with tabs[3]:
		_render_news_tab()


if __name__ == "__main__":
	main()
