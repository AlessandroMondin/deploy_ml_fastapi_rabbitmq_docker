# Loop to start each curl command in the background
for i in {1..50}; do
  sleep 0.05
  curl -X POST \
    "http://localhost:8000/predict/" \
    -F "file=@/Users/alessandro/rabbit-mq-exp/data/bus.txt" &
done

# Wait for all background jobs to finish
wait
echo "All requests completed"