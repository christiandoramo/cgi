Universidade Federal Rural de Pernambuco (UFRPE)
Departamento de Computação (DC)
Computação Gráfica Básica (06230)
1ª VA - Especificação
Carregar na memória uma malha de triângulos referente a um objeto 3D armazenada em
arquivo de texto e desenhar seus vértices na tela. O arquivo utilizado para armazenar uma
malha com 𝑛 vértices e 𝑘 triângulos possui o seguinte formato:
<nº de vértices> <nº de triângulos>
<coordenada 𝑥 do vértice 1> <coordenada 𝑦 do vértice 1> <coordenada 𝑧 do vértice 1>
<coordenada 𝑥 do vértice 2> <coordenada 𝑦 do vértice 2> <coordenada 𝑧 do vértice 2>
...
<coordenada 𝑥 do vértice 𝑛> <coordenada 𝑦 do vértice 𝑛> <coordenada 𝑧 do vértice 𝑛>
<índice do vértice 1 do triângulo 1> <índice do vértice 2 do triângulo 1> <índice do vértice 3 do triângulo 1>
<índice do vértice 1 do triângulo 2> <índice do vértice 2 do triângulo 2> <índice do vértice 3 do triângulo 2>
...
<índice do vértice 1 do triângulo 𝑘> <índice do vértice 2 do triângulo 𝑘> <índice do vértice 3 do triângulo 𝑘>
Exemplo de arquivo:
4 4
1 1 1
1 30 1
30 30 1
1 1 30
1 2 3
1 2 4
2 3 4
1 3 4
Uma vez que a malha foi carregada na memória, deve-se obter a projeção em perspectiva
de seus vértices.
A aplicação deverá carregar a partir de um arquivo de texto os seguintes parâmetros da
câmera virtual:
• Ponto 𝐶;
• Vetores 𝑁 e 𝑉;
• Escalares 𝑑, ℎ𝑥 e ℎ𝑦.
Exemplo de parâmetros de câmera:
𝑁 = 0 1 -1
𝑉 = 0 -1 -1
𝑑 = 5
ℎ𝑥 = 2
ℎ𝑦 = 2
𝐶 = 0 -500 500
O usuário deve ser capaz de alterar os valores dos parâmetros no arquivo de texto,
recarregá-los e redesenhar o objeto sem precisar fechar a aplicação e abri-la novamente
(ex: o usuário pode pressionar uma tecla específica para recarregar os parâmetros a partir
do arquivo de texto e redesenhar o objeto).
Deve-se converter os vértices do objeto de coordenadas mundiais para coordenadas de
vista, realizar a projeção em perspectiva, converter para coordenadas normalizadas e por
fim para coordenadas de tela. Após isso, deve-se utilizar o algoritmo de rasterização de
polígonos scan line conversion (varredura) para preencher os triângulos projetados. Os
pixels da tela correspondentes aos triângulos projetados e preenchidos devem ser pintados
de branco, enquanto que os demais pixels devem ser pintados de preto.
Qualquer linguagem de programação pode ser utilizada (C, Java, etc.). A única função
gráfica que pode ser utilizada é a que desenha um pixel colorido na tela. Apenas as
bibliotecas padrão da linguagem escolhida podem ser usadas.
Obs.: caso desejado, é permitido usar uma biblioteca externa que ofereça a função de pintar
um pixel colorido na tela.