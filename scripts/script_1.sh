for (( i=1; i<=100000000; i++ ))
do
  part1=$(($i * 191 % 256))
  part2=$(($i * 219 % 250))
  ip="10.0.$part1.$part2"
  date="@$((1557824751 + $i))"
  code=$((($i * 55 / 6 % 4 + 2) * 100 + ($i * 19 % 4)))
  echo '{"time":"'`date --date=$date +"%Y-%m-%d %H:%M:%S"`'","ip":"'$ip'","status_code":'$code'}'
done