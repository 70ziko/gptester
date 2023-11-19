#!/usr/bin/ruby
puts "Calculating"
first_number  = ARGV[0]
second_number = ARGV[1]
print "Args:",first_number,second_number,"\n"
first_number_int  = Integer(first_number) rescue nil
second_number_int = Integer(second_number) rescue nil
if first_number_int && second_number_int
  print first_number_int + second_number_int
else
  print "Invalid input! Please enter integers."
end
