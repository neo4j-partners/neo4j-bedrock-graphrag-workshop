"""
Typer CLI for validating the Lab 6 GraphRAG pipeline.

Commands:
    test   Run 6-phase validation (data loading, embeddings, vector,
           vector-cypher, fulltext, hybrid)
    chat   Interactive GraphRAG chat using HybridCypherRetriever
"""

from __future__ import annotations

import typer
from neo4j import GraphDatabase
from neo4j_graphrag.embeddings import BedrockEmbeddings
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import BedrockLLM
from rich.console import Console

from .config import Settings
from .data import (
    create_documents_and_chunks,
    create_fulltext_indexes,
    create_vector_idx,
    generate_embeddings,
)
from .retrievers import build_retrievers

app = typer.Typer(help="Validate GraphRAG retrievers against the SEC financial graph.")
console = Console()


def _banner(text: str) -> None:
    console.print()
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    console.print(f"[bold cyan]  {text}[/bold cyan]")
    console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")
    console.print()


def _phase(number: int, title: str) -> None:
    console.print(f"\n[bold yellow]Phase {number}: {title}[/bold yellow]")
    console.print("-" * 50)


def _ok(msg: str) -> None:
    console.print(f"  [green]OK[/green] {msg}")


def _fail(msg: str) -> None:
    console.print(f"  [red]FAIL[/red] {msg}")


# ── test command ────────────────────────────────────────────────────────────


@app.command()
def test() -> None:
    """Run 6-phase GraphRAG validation."""
    settings = Settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )
    data_dir = settings.resolved_data_dir

    try:
        driver.verify_connectivity()
        _banner("GraphRAG Validator -- SEC Financial Graph")
        console.print(f"  Neo4j URI: {settings.neo4j_uri}")
        console.print(f"  Model:     {settings.model_id}")
        console.print(f"  Embedder:  {settings.embedding_model_id}")
        console.print(f"  Region:    {settings.region}")

        embedder = BedrockEmbeddings(
            model_id=settings.embedding_model_id,
            region_name=settings.region,
        )
        llm = BedrockLLM(
            model_id=settings.model_id,
            region_name=settings.region,
        )

        # ── Phase 1: Data loading ───────────────────────────────────────
        _phase(1, "Data Loading (Document & Chunk nodes)")
        try:
            chunk_count = create_documents_and_chunks(driver, data_dir)
            _ok(f"Created {chunk_count} Chunk nodes with FROM_DOCUMENT + NEXT_CHUNK")
        except Exception as exc:
            _fail(f"Data loading failed: {exc}")
            raise typer.Exit(1)

        # ── Phase 2: Embeddings ─────────────────────────────────────────
        _phase(2, "Embedding Generation (Titan V2)")
        try:
            updated = generate_embeddings(driver, embedder)
            _ok(f"Generated embeddings for {updated} chunks")
        except Exception as exc:
            _fail(f"Embedding generation failed: {exc}")
            raise typer.Exit(1)

        # ── Phase 3: Vector index + retriever ───────────────────────────
        _phase(3, "Vector Retriever")
        try:
            create_vector_idx(driver)
            _ok("Created chunkEmbeddings vector index (1024 dims, cosine)")

            retrievers = build_retrievers(driver, embedder, llm)
            results = retrievers.vector.search(
                query_text="What products does Apple offer?", top_k=3
            )
            _ok(f"VectorRetriever returned {len(results.items)} results")
            for item in results.items:
                score = item.metadata.get("score", 0)
                text = (item.content or "")[:120]
                console.print(f"    score={score:.4f}  {text}...")
        except Exception as exc:
            _fail(f"Vector retriever failed: {exc}")
            raise typer.Exit(1)

        # ── Phase 4: Vector-Cypher retriever ────────────────────────────
        _phase(4, "Vector-Cypher Retriever")
        try:
            results = retrievers.vector_cypher.search(
                query_text="What risks does Apple face?", top_k=3
            )
            _ok(f"VectorCypherRetriever returned {len(results.items)} results")
            for item in results.items:
                score = item.metadata.get("score", 0)
                text = (item.content or "")[:120] if isinstance(item.content, str) else str(item.content)[:120]
                console.print(f"    score={score:.4f}  {text}...")
        except Exception as exc:
            _fail(f"Vector-Cypher retriever failed: {exc}")
            raise typer.Exit(1)

        # ── Phase 5: Fulltext indexes ───────────────────────────────────
        _phase(5, "Fulltext Indexes")
        try:
            create_fulltext_indexes(driver)
            _ok("Created search_chunks and search_entities fulltext indexes")

            # Quick verification
            with driver.session() as session:
                result = session.run(
                    "CALL db.index.fulltext.queryNodes('search_entities', 'Apple') "
                    "YIELD node, score "
                    "RETURN labels(node) AS labels, node.name AS name, score "
                    "LIMIT 3"
                )
                records = list(result)
                _ok(f"search_entities returned {len(records)} results for 'Apple'")
                for rec in records:
                    console.print(f"    [{rec['labels'][0]}] {rec['name']} (score={rec['score']:.4f})")
        except Exception as exc:
            _fail(f"Fulltext index creation failed: {exc}")
            raise typer.Exit(1)

        # ── Phase 6: Hybrid retriever ───────────────────────────────────
        _phase(6, "Hybrid-Cypher Retriever")
        try:
            results = retrievers.hybrid_cypher.search(
                query_text="artificial intelligence risks", top_k=3
            )
            _ok(f"HybridCypherRetriever returned {len(results.items)} results")
            for item in results.items:
                score = item.metadata.get("score", 0)
                text = (item.content or "")[:120] if isinstance(item.content, str) else str(item.content)[:120]
                console.print(f"    score={score:.4f}  {text}...")
        except Exception as exc:
            _fail(f"Hybrid retriever failed: {exc}")
            raise typer.Exit(1)

        _banner("All 6 phases passed")

    finally:
        driver.close()


# ── chat command ────────────────────────────────────────────────────────────


@app.command()
def chat() -> None:
    """Interactive GraphRAG chat using HybridCypherRetriever."""
    settings = Settings()
    driver = GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_username, settings.neo4j_password),
    )

    try:
        driver.verify_connectivity()
        _banner("GraphRAG Chat (HybridCypherRetriever)")
        console.print("Type your question and press Enter. Type 'quit' to exit.\n")

        embedder = BedrockEmbeddings(
            model_id=settings.embedding_model_id,
            region_name=settings.region,
        )
        llm = BedrockLLM(
            model_id=settings.model_id,
            region_name=settings.region,
        )

        retrievers = build_retrievers(driver, embedder, llm)
        rag = GraphRAG(llm=llm, retriever=retrievers.hybrid_cypher)

        while True:
            try:
                query = console.input("[bold green]You:[/bold green] ").strip()
            except (EOFError, KeyboardInterrupt):
                console.print("\nGoodbye!")
                break

            if not query or query.lower() in ("quit", "exit", "q"):
                console.print("Goodbye!")
                break

            try:
                response = rag.search(
                    query, retriever_config={"top_k": 5}, return_context=True
                )
                console.print(f"\n[bold blue]Assistant:[/bold blue] {response.answer}")
                console.print(
                    f"[dim](retrieved {len(response.retriever_result.items)} context items)[/dim]\n"
                )
            except Exception as exc:
                console.print(f"[red]Error:[/red] {exc}\n")

    finally:
        driver.close()


if __name__ == "__main__":
    app()
