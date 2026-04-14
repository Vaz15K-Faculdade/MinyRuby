puts "Digite n para o Triangulo de Pascal:"
n = gets

if n <= 0
  puts "Erro: n deve ser >= 1"
else
  linha = 0
  while linha < n do
    coluna = 0
    valor = 1
    while coluna <= linha do
      puts valor
      valor = valor * (linha - coluna) / (coluna + 1)
      coluna = coluna + 1
    end
    puts "---"
    linha = linha + 1
  end
end
