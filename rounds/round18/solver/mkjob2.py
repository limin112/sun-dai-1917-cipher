import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from june_data import null_msgs
from mkjob import write_job
k, model, path = sys.argv[1:4]
write_job(path, null_msgs(k), model, sys.argv[4:])
