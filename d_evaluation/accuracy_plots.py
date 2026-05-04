import pandas as pd
import matplotlib.pyplot as plt


def plot_accuracy_by_document(csv_path: str):
    """
    Plots average accuracy per document (record_id)
    """

    df = pd.read_csv(csv_path)

    # ensure numeric
    df["correct?"] = pd.to_numeric(df["correct?"], errors="coerce")

    doc_accuracy = (
        df.groupby("record_id")["correct?"]
        .mean()
        .reset_index()
        .sort_values("correct?")
    )

    plt.figure()
    plt.plot(doc_accuracy["record_id"], doc_accuracy["correct?"], marker="o")
    plt.xticks(rotation=90)
    plt.ylabel("Accuracy")
    plt.xlabel("Document (record_id)")
    plt.title("Model Accuracy per Document")
    plt.tight_layout()
    plt.show()