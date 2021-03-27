for (( i=1; i<=100000000; i++ ))
do
  part1=$(($i * 19 % 256))
  part2=$(($i * 37 % 250))
  ip="10.0.$part1.$part2"
  date="@$((1420063200 + $i * 2))"
  code=$((($i * 8 / 6 % 4 + 2) * 100 + ($i * 13 % 4)))
  echo '{"time":"'`date --date=$date +"%Y-%m-%d %H:%M:%S"`'","ip":"'$ip'","status_code":'$code'}'
done