import sys
import tempfile
from pathlib import Path

import streamlit as st

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


def _render_header():
	st.set_page_config(page_title=APP_TITLE, layout="wide")
	st.title(APP_TITLE)
	st.caption("Run specialized finance agents from a single interface.")


def _run_agent(executor, user_input: str) -> str:
	result = executor.invoke({"input": user_input})
	return result.get("output", "No output returned.")


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
			output = _run_agent(qa_executor, question)
		st.markdown(output)


def _render_portfolio_tab():
	st.subheader("Portfolio Analysis")
	st.write("Analyze your portfolio for allocation, risk, and diversification insights.")

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
			output = _run_agent(portfolio_executor, user_input)

		st.markdown(output)

		# Display charts directly from the analysis_output directory.
		# The portfolio_analysis_tool saves all PNGs there after every run.
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
			output = _run_agent(market_executor, request)
		st.markdown(output)


def _render_news_tab():
	st.subheader("News Synthesizer")
	st.write("Summarize market news, sentiment, and headlines.")

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
			output = _run_agent(news_executor, request)
		st.markdown(output)


def main():
	_render_header()

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
