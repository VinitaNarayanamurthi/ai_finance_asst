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


def _render_header():
	st.set_page_config(page_title=APP_TITLE, layout="wide")
	st.title(APP_TITLE)
	st.caption("Run specialized finance agents from a single interface.")


def _run_agent(executor, user_input: str) -> str:
	result = executor.invoke({"input": user_input})
	return result.get("output", "No output returned.")


def _render_finance_qa_tab():
	st.subheader("Finance Q&A")
	st.write("Ask questions grounded in your document knowledge base.")

	question = st.text_area("Question", placeholder="What are the key financial trends for 2024?")
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

	if st.button("Run Portfolio Analysis", type="primary"):
		if uploaded_file is not None:
			with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
				tmp_file.write(uploaded_file.read())
				file_path = tmp_file.name
		else:
			file_path = fallback_path

		user_input = f"Analyze my portfolio from {file_path} and give me insights."
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

	request = st.text_area("Request", placeholder="What's the current price of AAPL and its daily trend?")
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

	request = st.text_area("Request", placeholder="Summarize the latest news about Apple stock.")
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
