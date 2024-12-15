from setuptools import setup, find_packages

setup(
    name="sagan-workflow",
    version="0.1.0",
    description="AI-powered proposal generation workflow system",
    author="Ketan Kunkalikar",
    author_email="ketankunkalikar33@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "langchain",
        "langchain-huggingface",
        "langchain-community",
        "typing-extensions",
        "langgraph",
        "python-dotenv",
        "openai",
        "langchain-openai",
        "langgraph-checkpoint-sqlite",
        "black",
        "ipython",
        "langchain-groq",
        "chromadb>=0.5.15",
        "langchain-chroma>=0.1.4",
        "markdown>=3.7",
        "pdfkit>=1.0.0",
        "langchain-core>=0.3.16",
        "duckduckgo-search>=6.3.4",
        "pypdf>=5.1.0",
        "python-multipart>=0.0.17",
        "pyngrok>=7.2.1",
        "nest-asyncio>=1.6.0",
        "beautifulsoup4>=4.12.3",
        "pymupdf==1.22.5",
        "einops>=0.8.0",
        "sentence-transformers>=3.3.1",
        "pylatex>=1.4.2",
        "certifi>=2024.8.30",
        "requests[security]>=2.32.3",
        "pyopenssl>=24.3.0",
        "colorama",
    ],
    python_requires=">=3.11",
) 