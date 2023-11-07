import logging
import logging.handlers
from os import path
from datetime import timedelta, datetime

# [START import_module]

# The DAG object; we'll need this to instantiate a DAG

from airflow import DAG
# Operators; we need this to operate!

from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import SparkKubernetesSensor

from airflow.utils.dates import days_ago

# [END import_module]


# [START default_args]

# These args will get passed on to each operator

# You can override them on a per-task basis during operator initialization
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'max_active_runs': 1,
    'retries': 3
}
# [END default_args]

# Configure root logger to capture only DEBUG logs
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

# Create a separate handler for INFO and higher logs
info_handler = logging.StreamHandler()
info_handler.setLevel(logging.INFO)

# Create a filter to filter out logs below the DEBUG level
info_filter = logging.Filter()
info_filter.filter = lambda record: record.levelno >= logging.INFO

# Add the filter to the INFO handler
info_handler.addFilter(info_filter)

# Add the INFO handler to the root logger
root_logger.addHandler(info_handler)

with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as file:
    current_namespace = file.read()

# [START instantiate_dag]

dag = DAG(
    'Spark-pi-autowithkube-3.3.1',
    default_args=default_args,
    schedule_interval=None,
    tags=['example', 'spark'],
    params={
        'namespace': current_namespace,
    }
)

def submit_task():
    logger.debug('Submitting Spark application...')
    # Submit Spark application code

submit = SparkKubernetesOperator(
    task_id='spark_pi_3.3.1-submit',
    namespace=current_namespace,
    application_file="spark-auto-newconnection.yaml",
    kubernetes_conn_id="kubernetes_auto",
    do_xcom_push=True,
    dag=dag,
    api_group="sparkoperator.hpe.com",
    enable_impersonation_from_ldap_user=False
)

def monitor_task():
    logger.debug('Monitoring Spark application...')
    # Monitor Spark application code

sensor = SparkKubernetesSensor(
    task_id='spark_pi_monitor',
    namespace=current_namespace,
    application_name="{{ task_instance.xcom_pull(task_ids='spark_pi_3.3.1-submit')['metadata']['name'] }}",
    kubernetes_conn_id="kubernetes_auto",
    dag=dag,
    api_group="sparkoperator.hpe.com",
    attach_log=True
)

submit >> sensor