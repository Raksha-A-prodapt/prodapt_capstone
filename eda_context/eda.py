# import pandas as pd
# import numpy as np

# # ============================================================
# # 1. LOAD DATA
# # ============================================================

# FILE_PATH = "./data/5g_netops.csv"

# df = pd.read_csv(FILE_PATH)

# print("=" * 80)
# print("DATASET LOADED")
# print("=" * 80)

# print(f"Rows    : {df.shape[0]:,}")
# print(f"Columns : {df.shape[1]}")
# print()


# # ============================================================
# # 2. COLUMN NAMES + DATA TYPES
# # ============================================================

# print("=" * 80)
# print("COLUMN NAMES AND DATA TYPES")
# print("=" * 80)

# for col in df.columns:
#     print(f"{col} --> {df[col].dtype}")

# print()


# # ============================================================
# # 3. BASIC DATASET INFORMATION
# # ============================================================

# print("=" * 80)
# print("DATASET INFO")
# print("=" * 80)

# df.info()

# print()


# # ============================================================
# # 4. MISSING VALUES
# # ============================================================

# print("=" * 80)
# print("MISSING VALUES")
# print("=" * 80)

# missing = pd.DataFrame({
#     "column": df.columns,
#     "missing_count": df.isnull().sum().values,
#     "missing_percentage": (
#         df.isnull().mean().values * 100
#     ).round(2)
# })

# print(missing.to_string(index=False))

# print()


# # ============================================================
# # 5. DUPLICATES
# # ============================================================

# print("=" * 80)
# print("DUPLICATES")
# print("=" * 80)

# duplicate_count = df.duplicated().sum()

# print(f"Duplicate rows: {duplicate_count:,}")
# print(
#     f"Duplicate percentage: "
#     f"{(duplicate_count / len(df) * 100):.2f}%"
# )

# print()


# # ============================================================
# # 6. NUMERICAL COLUMNS
# # ============================================================

# numeric_cols = df.select_dtypes(
#     include=["int64", "float64", "int32", "float32"]
# ).columns.tolist()

# print("=" * 80)
# print("NUMERICAL COLUMNS")
# print("=" * 80)

# print(f"Number of numerical columns: {len(numeric_cols)}")
# print()

# print(df[numeric_cols].describe().T.to_string())

# print()


# # ============================================================
# # 7. CATEGORICAL / STRING COLUMNS
# # ============================================================

# categorical_cols = df.select_dtypes(
#     include=["object", "category", "string"]
# ).columns.tolist()

# print("=" * 80)
# print("CATEGORICAL COLUMNS")
# print("=" * 80)

# print(f"Number of categorical columns: {len(categorical_cols)}")
# print()

# for col in categorical_cols:
#     print("-" * 80)
#     print(f"COLUMN: {col}")
#     print(f"Unique count: {df[col].nunique(dropna=False)}")
#     print("Unique values:")

#     values = df[col].dropna().unique()

#     for value in values:
#         print(f"  - {value}")

# print()


# # ============================================================
# # 8. VALUE COUNTS FOR CATEGORICAL COLUMNS
# # ============================================================

# print("=" * 80)
# print("CATEGORICAL VALUE DISTRIBUTIONS")
# print("=" * 80)

# for col in categorical_cols:
#     print("-" * 80)
#     print(f"{col}")
#     print(
#         df[col]
#         .value_counts(dropna=False)
#         .to_string()
#     )

# print()


# # ============================================================
# # 9. NUMERICAL RANGE
# # ============================================================

# print("=" * 80)
# print("NUMERICAL RANGES")
# print("=" * 80)

# for col in numeric_cols:
#     print(
#         f"{col}: "
#         f"min={df[col].min()}, "
#         f"max={df[col].max()}, "
#         f"mean={df[col].mean():.4f}, "
#         f"median={df[col].median():.4f}"
#     )

# print()


# # ============================================================
# # 10. SKEWNESS
# # ============================================================

# print("=" * 80)
# print("NUMERICAL SKEWNESS")
# print("=" * 80)

# for col in numeric_cols:
#     print(f"{col}: {df[col].skew():.4f}")

# print()


# # ============================================================
# # 11. POTENTIAL CONSTANT COLUMNS
# # ============================================================

# print("=" * 80)
# print("CONSTANT / NEAR-CONSTANT COLUMNS")
# print("=" * 80)

# for col in df.columns:
#     unique_count = df[col].nunique(dropna=False)

#     if unique_count <= 1:
#         print(f"{col}: CONSTANT")

#     elif unique_count == 2:
#         print(f"{col}: Only 2 unique values")

# print()


# # ============================================================
# # 12. SAMPLE RECORDS
# # ============================================================

# print("=" * 80)
# print("SAMPLE RECORDS")
# print("=" * 80)

# print(df.head(10).to_string(index=False))

# print()


# # ============================================================
# # 13. RANDOM SAMPLE
# # ============================================================

# print("=" * 80)
# print("RANDOM SAMPLE")
# print("=" * 80)

# print(
#     df.sample(
#         min(10, len(df)),
#         random_state=42
#     ).to_string(index=False)
# )

# print()


# # ============================================================
# # 14. CORRELATION MATRIX
# # ============================================================

# print("=" * 80)
# print("NUMERICAL CORRELATION WITH FAULT OCCURRENCE RATE")
# print("=" * 80)

# target = "Fault Occurrence Rate (%)"

# if target in df.columns:

#     correlations = (
#         df[numeric_cols]
#         .corr()[target]
#         .sort_values(ascending=False)
#     )

#     print(correlations.to_string())

# else:
#     print(f"Target column '{target}' not found.")

# print()


# # ============================================================
# # 15. TARGET DISTRIBUTION
# # ============================================================

# print("=" * 80)
# print("FAULT OCCURRENCE RATE DISTRIBUTION")
# print("=" * 80)

# if target in df.columns:

#     print(df[target].describe().to_string())

#     print("\nPercentiles:")
#     print(
#         df[target]
#         .quantile([0, .01, .05, .10, .25, .50, .75, .90, .95, .99, 1])
#         .to_string()
#     )

# print()


# # ============================================================
# # 16. ISSUE REPORTED DISTRIBUTION
# # ============================================================

# if "Issue Reported" in df.columns:

#     print("=" * 80)
#     print("ISSUE REPORTED DISTRIBUTION")
#     print("=" * 80)

#     print(
#         df["Issue Reported"]
#         .value_counts(dropna=False)
#         .to_string()
#     )

# print()


# # ============================================================
# # 17. ALL COLUMNS — COMPACT SUMMARY
# # ============================================================

# print("=" * 80)
# print("COMPLETE COLUMN SUMMARY")
# print("=" * 80)

# summary = pd.DataFrame({
#     "column": df.columns,
#     "dtype": df.dtypes.astype(str).values,
#     "unique_values": [
#         df[col].nunique(dropna=False)
#         for col in df.columns
#     ],
#     "missing": [
#         df[col].isnull().sum()
#         for col in df.columns
#     ],
#     "missing_%": [
#         round(df[col].isnull().mean() * 100, 2)
#         for col in df.columns
#     ]
# })

# print(summary.to_string(index=False))

# print()
# print("=" * 80)
# print("EDA COMPLETE")
# print("=" * 80)

import pandas as pd
import numpy as np

FILE_PATH = "./data/5g_netops.csv"
OUTPUT_FILE = "eda_output.txt"

df = pd.read_csv(FILE_PATH)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    f.write("=== DATASET OVERVIEW ===\n")
    f.write(f"Rows: {len(df):,}\n")
    f.write(f"Columns: {len(df.columns)}\n\n")

    # Column information
    f.write("=== COLUMN INFORMATION ===\n")
    for col in df.columns:
        f.write(
            f"{col} | "
            f"dtype={df[col].dtype} | "
            f"unique={df[col].nunique(dropna=False)} | "
            f"missing={df[col].isna().sum()} "
            f"({df[col].isna().mean()*100:.2f}%)\n"
        )

    # Numerical columns
    numeric_cols = df.select_dtypes(
        include=["int64", "float64", "int32", "float32"]
    ).columns

    f.write("\n=== NUMERICAL COLUMNS ===\n")
    for col in numeric_cols:
        f.write(
            f"{col} | "
            f"min={df[col].min()} | "
            f"max={df[col].max()} | "
            f"mean={df[col].mean():.4f} | "
            f"median={df[col].median():.4f}\n"
        )

    # Categorical columns
    categorical_cols = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns

    f.write("\n=== CATEGORICAL VALUES ===\n")
    for col in categorical_cols:
        f.write(f"\n{col}:\n")
        for value in sorted(df[col].dropna().unique().astype(str)):
            f.write(f"  - {value}\n")

    # Target information
    target = "Fault Occurrence Rate (%)"

    if target in df.columns:
        f.write("\n=== FAULT OCCURRENCE RATE ===\n")
        f.write(
            df[target]
            .describe()
            .to_string()
        )
        f.write("\n")

    # Sample rows
    f.write("\n=== SAMPLE DATA ===\n")
    f.write(
        df.head(5).to_string(index=False)
    )

print(f"EDA saved to: {OUTPUT_FILE}")