
   
spark-submit \
    --master yarn \
    --deploy-mode cluster \
    test17.py \
    --output $1 
