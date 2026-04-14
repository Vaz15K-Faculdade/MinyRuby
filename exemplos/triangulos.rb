puts "Digite o lado a:"
a = gets
puts "Digite o lado b:"
b = gets
puts "Digite o lado c:"
c = gets

if a <= 0 || b <= 0 || c <= 0
  puts "Medidas invalidas"
else
  if a + b > c && a + c > b && b + c > a
    if a == b && b == c
      puts "Triangulo equilatero valido"
    else
      if a == b || a == c || b == c
        puts "Triangulo isosceles valido"
      else
        puts "Triangulo escaleno valido"
      end
    end
  else
    puts "Medidas invalidas"
  end
end
