spark-submit \
    --master yarn \
    --deploy-mode cluster \
    --num-executors 3 \
    --py-files test.py \
    --output $1 
