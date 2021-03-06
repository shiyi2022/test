# -*- coding: utf-8 -*-
"""test8

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1x9mgt3LOIoKgt5mwyJmL0duyFYgGSPMS
"""

#!pip install pyspark

from pyspark.sql import SparkSession
from pyspark import SparkConf, SparkContext
from pyspark.sql.functions import explode
import argparse

spark = SparkSession \
    .builder \
    .appName("COMP5349 A2") \
    .getOrCreate()

#spark.sparkContext.setLogLevel("ERROR")

#spark_conf = SparkConf()\
    # .setAppName("assignment2")

#sc=SparkContext.getOrCreate(spark_conf) 

#parser = argparse.ArgumentParser()
#parser.add_argument("--output", help="the output path",
                        #default='assignment2_out')
#args = parser.parse_args()
#output_path = args.output

#rating_data = 's3://comp5349-data/week6/ratings.csv'

test_init_df = spark.read.json('test.json',multiLine=True)

test_init_df.printSchema()

#展平嵌套数据
test_data_df= test_init_df.select((explode('data').alias('data')))\
                          .select('data.title',(explode('data.paragraphs').alias('paragraphs')))\
                          .select('title','paragraphs.context', explode('paragraphs.qas').alias('qas'))\
                          .select('title','context','qas.question','qas.is_impossible','qas.id','qas.answers')

test_data_df.printSchema()
test_data_df.take(1)

#样本分类
# is_impossible=True
data_ture=test_data_df.where("is_impossible=True").select('title',"context",'id','question','is_impossible')

#is_impossible=False
data_false=test_data_df.where("is_impossible=False")\
                      .select('title',"context",'id','question','is_impossible', explode("answers").alias('answers'))\
                      .select('title',"context",'id','question','is_impossible', 'answers.answer_start','answers.text')



data_ture.count()
data_false.count()

#长文本分割

def split_rdd(line):
     
     title,comtext,id,question,is_impossible=line
     length=len(comtext)
     a=(length//2048)+1
     b=[]
     for i in range(a):
          c=[]
          if i*2048+4096<length:
             cc=comtext[i*2048:i*2048+4096]
             c.append(title)
             c.append(cc)
             c.append(i)
             c.append(id)
             c.append(question)
          else:
             cc=comtext[i*2048:length]
             c.append(title)
             c.append(cc)
             c.append(i)
             c.append(id)
             c.append(question)
          b.append(c)
     return b


def split_rdd2(line):
     
     title,context,id,question,is_impossible,answer_start,text=line
     length=len(context)
     a=(length//2048)+1
     length_text=len(text)
     start_index=max(0,(answer_start//2048)-1)
     end_index=(answer_start+length_text)//2048
     b=[]
     for i in range(a):
          c=[]
          if i*2048+4096<length:
             cc=context[i*2048:i*2048+4096]
             c.append(title)
             c.append(cc)
             c.append(i)
             c.append(id)
             c.append(question)
             c.append(start_index)
             c.append(end_index)
             c.append(answer_start)
             c.append(text)
          else:
             cc=context[i*2048:length]
             c.append(title)
             c.append(cc)
             c.append(i)
             c.append(id)
             c.append(question)
             c.append(start_index)
             c.append(end_index)
             c.append(answer_start)
             c.append(text)
          b.append(c)
     return b

# impossible samples
a=data_ture.rdd
impossible_samples=a.flatMap(split_rdd)
impossible_samples.count()

#posivle samples + positive samples
aaa=data_false.rdd
ccc=aaa.flatMap(split_rdd2)

##positive
def positive(line):
     
     title,context,index,id,question,start_index,end_index,answer_start,text=line
     if start_index<=index and index<=end_index:
       return title,context,index,id,question,start_index,end_index,answer_start,text

def positive2(line):
     
     title,context,index,id,question,start_index,end_index,answer_start,text=line
     a=answer_start-index*2048
     b=a+len(text)
     answer_start=max(0,a)
     answer_end=min(b,4096)
     
     return title,context,index,id,question,answer_start,answer_end

positive_samples=ccc.map(positive)\
                    .filter( lambda x: x is not None)\
                    .map(positive2)
positive_samples.count()

# possible negative

def possible_negative(line):
     
     title,context,index,id,question,start_index,end_index,answer_start,text=line
     if start_index>index or index>end_index:
       return title,context,index,id,question

possible_negative_samples=ccc.map(possible_negative)\
                             .filter( lambda x: x is not None)

possible_negative_samples.count()

#output
def chose_schema(line):
  title,context,index,id,question,answer_start,answer_end=line
  return context,question,answer_start,answer_end

positive=positive_samples.map(chose_schema).toDF()
samples=positive.withColumnRenamed("_1", "context")\
                .withColumnRenamed("_2", "question")\
                .withColumnRenamed("_3", "answer_start")\
                .withColumnRenamed("_4", "answer_end")

samples.coalesce(1).write.json("samples.json")



