import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, lower, trim, regexp_replace, split, lit, when,
    monotonically_increasing_id, coalesce, to_timestamp, row_number
)
from pyspark.sql.window import Window

# =========================================
# Glue Job Initialization
# =========================================
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# =========================================
# Paths (edit these or pass as parameters)
# =========================================
zoominfo_path     = "s3://your-bucket/zoominfo.csv"
osc_accounts_path = "s3://your-bucket/osc_accounts.csv"
final_output_path = "s3://your-bucket/output/match_results"

# =========================================
# Helpers
# =========================================
def extract_domain(df, colname):
    return (
        df.withColumn(colname, lower(trim(col(colname))))
          .withColumn(colname, regexp_replace(col(colname), r"^https?://", ""))
          .withColumn(colname, regexp_replace(col(colname), r"^ftp://", ""))
          .withColumn(colname, regexp_replace(col(colname), r"^www\.", ""))
          .withColumn(colname, split(col(colname), "/").getItem(0))
          .withColumn(colname, split(col(colname), "\\?").getItem(0))
    )

def clean_string_cols(df, exclude=()):
    string_cols = {name for name, dtype in df.dtypes if dtype == "string"}
    projected = []
    for c in df.columns:
        if c in exclude:
            projected.append(col(c))
        elif c in string_cols:
            projected.append(trim(lower(col(c))).alias(c))
        else:
            projected.append(col(c))
    return df.select(projected)

def non_empty(c):
    return col(c).isNotNull() & (trim(col(c)) != "")

# =========================================
# Load
# =========================================
zi  = spark.read.csv(zoominfo_path, header=True, inferSchema=True)
osc = spark.read.csv(osc_accounts_path, header=True, inferSchema=True)

# =========================================
# Parse created_date
# =========================================
osc = osc.withColumn(
    "osc_created_dt",
    coalesce(
        to_timestamp(col("created_date")),
        to_timestamp(col("created_date"), "yyyy-MM-dd"),
        to_timestamp(col("created_date"), "yyyy/MM/dd"),
        to_timestamp(col("created_date"), "MM/dd/yyyy"),
        to_timestamp(col("created_date"), "yyyy-MM-dd HH:mm:ss"),
        to_timestamp(col("created_date"), "MM/dd/yyyy HH:mm:ss")
    )
)

# =========================================
# Extract domain + clean strings
# =========================================
zi  = extract_domain(zi,  "website").withColumnRenamed("website", "website_domain")
osc = extract_domain(osc, "website").withColumnRenamed("website", "website_domain")

zi  = clean_string_cols(zi)
osc = clean_string_cols(osc, exclude=("osc_created_dt",))

zi_cols = zi.columns
zi = zi.withColumn("zi_rowid", monotonically_increasing_id())

zi_a  = zi.alias("zi")
osc_a = osc.alias("osc")

# =========================================
# Match Conditions
# =========================================
cond_contactid = (
    non_empty("zi.contactid") & non_empty("osc.contactid") &
    (col("zi.contactid") == col("osc.contactid"))
)
cond_domain = (
    non_empty("zi.website_domain") & non_empty("osc.website_domain") &
    (col("zi.website_domain") == col("osc.website_domain"))
)
cond_name_state = (
    non_empty("zi.account_name") & non_empty("zi.state") &
    non_empty("osc.account_name") & non_empty("osc.state") &
    (col("zi.account_name") == col("osc.account_name")) &
    (col("zi.state") == col("osc.state"))
)

# =========================================
# Join
# =========================================
joined = zi_a.join(
    osc_a,
    on=(cond_contactid | cond_domain | cond_name_state),
    how="left"
)

# =========================================
# Match Flags
# =========================================
joined = (
    joined
    .withColumn("is_contactid_match", cond_contactid)
    .withColumn("is_domain_match", (~col("is_contactid_match")) & cond_domain)
    .withColumn("is_name_state_match", (~col("is_contactid_match")) & (~col("is_domain_match")) & cond_name_state)
    .withColumn(
        "match_rule",
        when(col("is_contactid_match"),  lit("ContactID"))
        .when(col("is_domain_match"),    lit("WebsiteDomain"))
        .when(col("is_name_state_match"),lit("AccountName+State"))
        .otherwise(lit("NoMatch"))
    )
    .withColumn(
        "match_flag",
        when(col("match_rule") == "NoMatch", lit("NO_MATCH")).otherwise(lit("MATCH"))
    )
    .withColumn(
        "match_priority",
        when(col("match_rule") == "ContactID",          lit(1))
        .when(col("match_rule") == "WebsiteDomain",     lit(2))
        .when(col("match_rule") == "AccountName+State", lit(3))
        .otherwise(lit(999))
    )
)

# =========================================
# Tie-breaker
# =========================================
try:
    order_cols = [col("match_priority").asc(), col("osc.osc_created_dt").asc_nulls_last()]
except AttributeError:
    order_cols = [
        col("match_priority").asc(),
        coalesce(col("osc.osc_created_dt"), to_timestamp(lit("9999-12-31 23:59:59"))).asc()
    ]

w = Window.partitionBy("zi_rowid").orderBy(*order_cols)
ranked = joined.withColumn("rn", row_number().over(w))
best = ranked.filter(col("rn") == 1)

# =========================================
# Final Output
# =========================================
final_df = best.select(*[col(f"zi.{c}").alias(c) for c in zi_cols] + ["match_flag", "match_rule"])
final_df.write.mode("overwrite").option("header", True).csv(final_output_path)

print("Glue job completed. Results written to S3.")
job.commit()
