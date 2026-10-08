from agents.query_agent import QueryAgent


def main():

    print("=" * 70)
    print("TELECOM NETWORK QUERY AGENT")
    print("=" * 70)

    # Initialize Query Agent
    agent = QueryAgent()

    # User query
    query = input(
        "\nEnter your telecom network query: "
    ).strip()

    if not query:
        print("Query cannot be empty.")
        return

    # Run Query Agent
    result = agent.run(
        query=query,
        top_k=5
    )

    # ========================================================
    # DISPLAY QUERY
    # ========================================================

    print("\n" + "=" * 70)
    print("QUERY")
    print("=" * 70)

    print(result["query"])

    print("\n" + "=" * 70)
    print("NETWORK ANALYSIS AND RECOMMENDATIONS")
    print("=" * 70)
    print(
        result.get("answer")
        or "Analysis is unavailable for this query."
    )

    # ========================================================
    # DISPLAY QUERY PLAN
    # ========================================================

    print("\n" + "=" * 70)
    print("QUERY PLAN")
    print("=" * 70)

    print(result["query_plan"])

    # ========================================================
    # DISPLAY RETRIEVAL INFORMATION
    # ========================================================

    print("\n" + "=" * 70)
    print("RETRIEVAL INFORMATION")
    print("=" * 70)

    print(
        f"Candidate Count: "
        f"{result['candidate_count']}"
    )

    print(
        f"BM25 Used: "
        f"{result['retrieval']['bm25_used']}"
    )

    print(
        f"Semantic Search Used: "
        f"{result['retrieval']['semantic_used']}"
    )

    print(
        f"Metadata Filter Used: "
        f"{result['retrieval']['metadata_filter_used']}"
    )

    print(
        f"Numeric Filter Used: "
        f"{result['retrieval']['numeric_filter_used']}"
    )

    classification = result.get("classification") or {}
    if classification:
        print("\n" + "=" * 70)
        print("INCIDENT CLASSIFICATION")
        print("=" * 70)
        print(
            f"Highest Priority: "
            f"{classification['highest_priority']}"
        )
        print(
            f"Priority Counts: "
            f"{classification['priority_counts']}"
        )

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    print("\n" + "=" * 70)
    print("TOP HISTORICAL INCIDENTS")
    print("=" * 70)

    results = result["results"]

    if not results:

        print(
            "\nNo matching historical incidents found."
        )

        return

    for index, item in enumerate(
        results,
        start=1
    ):

        print(
            f"\n--- Result {index} ---"
        )

        print(
            f"Incident ID: "
            f"{item['incident_id']}"
        )

        incident_classification = item.get("classification") or {}
        if incident_classification:
            print(
                f"Priority: "
                f"{incident_classification['priority']} "
                f"({incident_classification['priority_level']})"
            )
            print(
                f"Classification: "
                f"{', '.join(incident_classification['labels']) or 'no threshold flags'}"
            )
            fault_prediction = incident_classification.get(
                "fault_prediction",
                {},
            )
            if fault_prediction.get("status") == "experimental":
                print(
                    "Experimental Model Fault Estimate: "
                    f"{fault_prediction['predicted_fault_occurrence_rate_percent']:.2f}% "
                    f"({fault_prediction['risk_band']}; "
                    "does not set priority)"
                )

        print(
            f"Hybrid Score: "
            f"{item['scores']['hybrid']:.4f}"
        )

        print(
            f"BM25 Score: "
            f"{item['scores']['bm25']:.4f}"
        )

        print(
            f"Semantic Score: "
            f"{item['scores']['semantic']:.4f}"
        )

        print("\nIncident Record:")

        for field, value in (
            item["incident"].items()
        ):

            print(
                f"  {field}: {value}"
            )


if __name__ == "__main__":
    main()