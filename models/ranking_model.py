def rank_candidates(candidates):
    """
    Sort candidates from highest score to lowest score.
    """

    ranked_candidates = sorted(
        candidates,
        key=lambda x: x["final_score"],
        reverse=True
    )

    return ranked_candidates