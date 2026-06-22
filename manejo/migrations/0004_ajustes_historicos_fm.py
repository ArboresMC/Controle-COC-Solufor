from django.db import migrations
from datetime import date


AJUSTES_HISTORICOS = [
    {'cnpj': '23.484.679/0001-37', 'propriedade': 'Capão do Tigre', 'especie': 'Pinus taeda', 'volume_ja_vendido': 7738.24},
    {'cnpj': 'PENDENTE-003', 'propriedade': 'Camargo', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 20940.0},
    {'cnpj': '33.285.403/0001-83', 'propriedade': 'Xadrez', 'especie': 'Pinus taeda', 'volume_ja_vendido': 57801.26},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Lageado de Cima', 'especie': 'Pinus taeda', 'volume_ja_vendido': 14721.11},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Nova II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 8935.636},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Santa Angela', 'especie': 'Pinus taeda', 'volume_ja_vendido': 44931.885},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Santa Helena', 'especie': 'Pinus taeda', 'volume_ja_vendido': 427.63},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Vicinal 7-II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 529.33},
    {'cnpj': '00.883.416/0001-03', 'propriedade': 'Paraíso', 'especie': 'Pinus sp', 'volume_ja_vendido': 2480.48},
    {'cnpj': '00.883.416/0001-03', 'propriedade': 'Paraíso', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 2021.95},
    {'cnpj': '78.549.615/0001-69', 'propriedade': 'Sossego', 'especie': 'Pinus taeda', 'volume_ja_vendido': 14729.49},
    {'cnpj': '78.549.615/0001-69', 'propriedade': 'Sossego I e II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 5588.66},
    {'cnpj': '78.549.615/0001-69', 'propriedade': 'Sossego I e II', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 3064.84},
    {'cnpj': '78.549.615/0001-69', 'propriedade': 'Sossego III', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 2268.15},
    {'cnpj': '02.058.184/0001-76', 'propriedade': 'Caraúno', 'especie': 'Pinus taeda', 'volume_ja_vendido': 17055.71},
    {'cnpj': '02.058.184/0001-76', 'propriedade': 'Morro Grande', 'especie': 'Pinus taeda', 'volume_ja_vendido': 3935.61},
    {'cnpj': '02.058.184/0001-76', 'propriedade': 'Rondinha', 'especie': 'Pinus taeda', 'volume_ja_vendido': 21291.57},
    {'cnpj': '003.960.019-04', 'propriedade': 'Adriana II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 4200.0},
    {'cnpj': 'PENDENTE-007', 'propriedade': 'Tamanduá', 'especie': 'Pinus taeda', 'volume_ja_vendido': 65804.82},
    {'cnpj': 'PENDENTE-007', 'propriedade': 'Tamanduá', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 260.0},
    {'cnpj': '00.060.274/0001-76', 'propriedade': 'Santa Joana', 'especie': 'Pinus taeda', 'volume_ja_vendido': 60321.75},
    {'cnpj': '00.060.274/0001-76', 'propriedade': 'Santa Joana', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 2275.41},
    {'cnpj': 'PENDENTE-009', 'propriedade': 'Água Branca', 'especie': 'Pinus taeda', 'volume_ja_vendido': 21916.73},
    {'cnpj': 'PENDENTE-009', 'propriedade': 'Ribeirão das Areias 1', 'especie': 'Pinus sp', 'volume_ja_vendido': 32516.49},
    {'cnpj': '35.158.618/0001-69', 'propriedade': 'Campos Verdes Unidos', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 3140.46},
    {'cnpj': 'PENDENTE-010', 'propriedade': 'Santana', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 59629.0},
    {'cnpj': '437.660.480-15', 'propriedade': 'Alegrete', 'especie': 'Pinus taeda', 'volume_ja_vendido': 18033.98},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Bom Sucesso A', 'especie': 'Pinus taeda', 'volume_ja_vendido': 32463.46},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Do Salto', 'especie': 'Pinus taeda', 'volume_ja_vendido': 7535.572},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Santa Clara', 'especie': 'Pinus taeda', 'volume_ja_vendido': 27801.45},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Santa Clara D', 'especie': 'Pinus taeda', 'volume_ja_vendido': 17915.03},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Santa Tereza', 'especie': 'Pinus taeda', 'volume_ja_vendido': 35176.04},
    {'cnpj': '79.441.168/0001-92', 'propriedade': 'Santana do Pitanga', 'especie': 'Pinus taeda', 'volume_ja_vendido': 152247.655},
    {'cnpj': '08.248.364/0001-05', 'propriedade': 'Boa Vista', 'especie': 'Pinus taeda', 'volume_ja_vendido': 2849.16},
    {'cnpj': 'PENDENTE-012', 'propriedade': 'São Pedro', 'especie': 'Pinus taeda', 'volume_ja_vendido': 1102.94},
    {'cnpj': 'PENDENTE-013', 'propriedade': 'Das Pedras', 'especie': 'Pinus sp', 'volume_ja_vendido': 35350.23},
    {'cnpj': '54.964.725/0001-29', 'propriedade': 'Flona de Irati', 'especie': 'Pinus taeda', 'volume_ja_vendido': 22013.0},
    {'cnpj': '14.792.934/0001-18', 'propriedade': 'ABC', 'especie': 'Eucalyptus', 'volume_ja_vendido': 14848.04},
    {'cnpj': '14.792.934/0001-18', 'propriedade': 'Aliança', 'especie': 'Eucalyptus', 'volume_ja_vendido': 1574.46},
    {'cnpj': '06.325.423/0001-68', 'propriedade': 'Residência Fuck', 'especie': 'Pinus taeda', 'volume_ja_vendido': 64454.85},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'Vale do Jotuva XI', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 1026.48},
    {'cnpj': 'PENDENTE-016', 'propriedade': 'Niasi', 'especie': 'Pinus taeda', 'volume_ja_vendido': 15000.0},
    {'cnpj': 'PENDENTE-017', 'propriedade': 'Rio Bonito I', 'especie': 'Pinus taeda', 'volume_ja_vendido': 158681.057},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'Califórnia', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 59116.99},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'Porta do Céu', 'especie': 'Eucalyptus urograndis', 'volume_ja_vendido': 6907.92},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'São José do Faxinal', 'especie': 'Eucalyptus urograndis', 'volume_ja_vendido': 32631.52},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'São José do Faxinal', 'especie': 'Pinus taeda', 'volume_ja_vendido': 8112.62},
    {'cnpj': '76.107.770/0019-29', 'propriedade': 'São Pedro', 'especie': 'Pinus taeda', 'volume_ja_vendido': 1266.71},
    {'cnpj': '10.887.398/0001-83', 'propriedade': 'São Bento', 'especie': 'Pinus taeda', 'volume_ja_vendido': 23709.0},
    {'cnpj': '00.149.821/0001-94', 'propriedade': 'São Joaquim', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 7690.26},
    {'cnpj': '00.149.821/0001-94', 'propriedade': 'São Joaquim', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 2723.68},
    {'cnpj': '53.548.361/0002-14', 'propriedade': 'Rondinha', 'especie': 'Pinus taeda', 'volume_ja_vendido': 32916.04},
    {'cnpj': '08.732.926/0001-83', 'propriedade': 'Horongozo - Rio Saltinho', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 3664.2},
    {'cnpj': '08.732.926/0001-83', 'propriedade': 'Cristiano VR - Alto Molungu', 'especie': 'Pinus sp', 'volume_ja_vendido': 4260.91},
    {'cnpj': '08.732.926/0001-83', 'propriedade': 'LG - Capitão Mohr', 'especie': 'Pinus sp', 'volume_ja_vendido': 4358.3},
    {'cnpj': '01.099.739/0005-99', 'propriedade': 'Brilhante XX', 'especie': 'Pinus sp', 'volume_ja_vendido': 1525.85},
    {'cnpj': '01.099.739/0005-99', 'propriedade': 'Morro Grande & Lagoa', 'especie': 'Pinus sp', 'volume_ja_vendido': 29573.86},
    {'cnpj': '01.099.739/0005-99', 'propriedade': 'Laranjeiras', 'especie': 'Eucalyptus urograndis', 'volume_ja_vendido': 33440.58},
    {'cnpj': 'PENDENTE-024', 'propriedade': 'Santa Luzia', 'especie': 'Pinus taeda', 'volume_ja_vendido': 7030.0},
    {'cnpj': '08.396.358/0007-82', 'propriedade': 'Fazenda Nova Piracicaba', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 188.11},
    {'cnpj': '08.396.358/0007-82', 'propriedade': 'Fazenda São Petrônio', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 433.35},
    {'cnpj': '34.446.573/0001-65', 'propriedade': 'Geyer', 'especie': 'Pinus sp', 'volume_ja_vendido': 148076.45},
    {'cnpj': '10.768.360/0001-91', 'propriedade': 'Dorizon', 'especie': 'Pinus taeda', 'volume_ja_vendido': 6509.351},
    {'cnpj': '10.768.360/0001-91', 'propriedade': 'Potinga', 'especie': 'Pinus taeda', 'volume_ja_vendido': 2063.36},
    {'cnpj': '10.768.360/0001-91', 'propriedade': 'Vidal', 'especie': 'Pinus taeda', 'volume_ja_vendido': 6258.794},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Areia Branca', 'especie': 'Pinus sp', 'volume_ja_vendido': 1573.57},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Barra I', 'especie': 'Pinus sp', 'volume_ja_vendido': 9862.45},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Charqueada Paulista', 'especie': 'Pinus sp', 'volume_ja_vendido': 1017.1},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Nivaldo', 'especie': 'Pinus sp', 'volume_ja_vendido': 548.78},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Pontilhão', 'especie': 'Pinus sp', 'volume_ja_vendido': 3805.68},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Ruppel', 'especie': 'Pinus sp', 'volume_ja_vendido': 494.53},
    {'cnpj': '78.897.600/0002-72', 'propriedade': 'Zawadzki', 'especie': 'Pinus sp', 'volume_ja_vendido': 1019.23},
    {'cnpj': '12.442.230/0001-90', 'propriedade': 'Ozório de Almeida Taques', 'especie': 'Pinus sp', 'volume_ja_vendido': 1200.0},
    {'cnpj': 'PENDENTE-025', 'propriedade': 'Sítio Monjolinho', 'especie': 'Pinus sp', 'volume_ja_vendido': 1308.04},
    {'cnpj': 'PENDENTE-025', 'propriedade': 'Sítio Arapinus', 'especie': 'Pinus sp', 'volume_ja_vendido': 40.0},
    {'cnpj': '05.552.102/0001-33', 'propriedade': 'Faxinal', 'especie': 'Pinus sp', 'volume_ja_vendido': 65140.96},
    {'cnpj': '390.083.632-91', 'propriedade': 'Campina da Alegria', 'especie': 'Eucalyptus saligna', 'volume_ja_vendido': 7966.2},
    {'cnpj': '390.083.632-91', 'propriedade': 'Sítio Cachoeirão 2', 'especie': 'Eucalyptus grandis', 'volume_ja_vendido': 2270.6},
    {'cnpj': '10.319.233/0001-05', 'propriedade': 'Martins', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 18147.35},
    {'cnpj': '10.319.233/0001-05', 'propriedade': 'Socorro', 'especie': 'Pinus sp', 'volume_ja_vendido': 8133.53},
    {'cnpj': '75.596.106/0001-07', 'propriedade': 'Cino Matão', 'especie': 'Pinus sp', 'volume_ja_vendido': 11531.604},
    {'cnpj': '75.596.106/0001-07', 'propriedade': 'Santa Teresa', 'especie': 'Eucalyptus', 'volume_ja_vendido': 20058.769},
    {'cnpj': '75.596.106/0001-07', 'propriedade': 'Formigas', 'especie': 'Pinus sp', 'volume_ja_vendido': 13580.86},
    {'cnpj': '75.596.106/0001-07', 'propriedade': 'Santa Clara II', 'especie': 'Eucalyptus', 'volume_ja_vendido': 3393.86},
    {'cnpj': 'PENDENTE-026', 'propriedade': 'Trieste', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 22226.05},
    {'cnpj': 'PENDENTE-029', 'propriedade': 'Campina da Alegria', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 4236.28},
    {'cnpj': '74.058.710/0001-09', 'propriedade': 'Alegria III', 'especie': 'Pinus sp', 'volume_ja_vendido': 18741.88},
    {'cnpj': '74.058.710/0001-09', 'propriedade': 'Boa Vista', 'especie': 'Pinus sp', 'volume_ja_vendido': 31209.78},
    {'cnpj': '74.058.710/0001-09', 'propriedade': 'Das Pedras', 'especie': 'Pinus sp', 'volume_ja_vendido': 35350.23},
    {'cnpj': '74.058.710/0001-09', 'propriedade': 'Fazenda Nossa Senhora da Luz', 'especie': 'Pinus sp', 'volume_ja_vendido': 21843.17},
    {'cnpj': '08.349.614/0001-95', 'propriedade': 'Funil', 'especie': 'Pinus taeda', 'volume_ja_vendido': 2330.0},
    {'cnpj': '08.349.614/0001-95', 'propriedade': 'Funil', 'especie': 'Eucalyptus saligna', 'volume_ja_vendido': 440.9},
    {'cnpj': '08.349.614/0001-95', 'propriedade': 'Funil', 'especie': 'Eucalyptus urograndis', 'volume_ja_vendido': 25474.0},
    {'cnpj': '43.446.111/0003-09', 'propriedade': 'América do Sul', 'especie': 'Eucalyptus urograndis', 'volume_ja_vendido': 179.0},
    {'cnpj': '43.446.111/0003-09', 'propriedade': 'Fazenda Alto Vale', 'especie': 'Pinus taeda', 'volume_ja_vendido': 1863.0},
    {'cnpj': '43.446.111/0003-09', 'propriedade': 'Sítio Paraíso', 'especie': 'Pinus taeda', 'volume_ja_vendido': 3295.0},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Palmital - Quinhão I', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 9103.2234},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Palmital - Quinhão I', 'especie': 'Pinus taeda', 'volume_ja_vendido': 67538.78},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Palmital II', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 12708.0},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Palmital II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 91429.0},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Serra da Esperança I', 'especie': 'Pinus taeda', 'volume_ja_vendido': 6888.0},
    {'cnpj': 'PENDENTE-033', 'propriedade': 'Serra da Esperança II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 7205.0},
    {'cnpj': '89.076.277/0002-92', 'propriedade': 'Sul I', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 117140.33},
    {'cnpj': '76.909.530/0001-19', 'propriedade': 'Cachoeira', 'especie': 'Pinus taeda', 'volume_ja_vendido': 200.39},
    {'cnpj': '76.909.530/0001-19', 'propriedade': 'Cantagalo', 'especie': 'Pinus taeda', 'volume_ja_vendido': 5613.65},
    {'cnpj': '76.909.530/0001-19', 'propriedade': 'Faxinal dos Carpinteiros', 'especie': 'Pinus taeda', 'volume_ja_vendido': 10232.37},
    {'cnpj': '76.909.530/0001-19', 'propriedade': 'Gabiroba', 'especie': 'Pinus taeda', 'volume_ja_vendido': 8940.45},
    {'cnpj': '76.909.530/0001-19', 'propriedade': 'Jacutinga', 'especie': 'Pinus taeda', 'volume_ja_vendido': 18621.14},
    {'cnpj': '906.759.247-15', 'propriedade': 'Águas Claras', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 15876.85},
    {'cnpj': '906.759.247-15', 'propriedade': 'Chácara Bananal', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 3841.79},
    {'cnpj': 'PENDENTE-034', 'propriedade': 'Barreiros', 'especie': 'Pinus taeda', 'volume_ja_vendido': 6980.63},
    {'cnpj': '46.421.786/0001-11', 'propriedade': 'Cerro Lindo', 'especie': 'Pinus taeda', 'volume_ja_vendido': 11643.53},
    {'cnpj': '46.421.786/0001-11', 'propriedade': 'Cerro Lindo', 'especie': 'Pinus elliottii', 'volume_ja_vendido': 243.36},
    {'cnpj': 'PENDENTE-035', 'propriedade': 'Niasi', 'especie': 'Pinus taeda', 'volume_ja_vendido': 7500.0},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Bugio', 'especie': 'Pinus taeda', 'volume_ja_vendido': 24864.73},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Bugio', 'especie': 'Eucalyptus dunnii', 'volume_ja_vendido': 8983.64},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Rio Corrente', 'especie': 'Pinus taeda', 'volume_ja_vendido': 25263.2475},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Colonia 3 - II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 789.26},
    {'cnpj': '057.349.409-68', 'propriedade': 'Araça', 'especie': 'Pinus taeda', 'volume_ja_vendido': 408.865},
    {'cnpj': '057.349.409-68', 'propriedade': 'Lopuch', 'especie': 'Pinus taeda', 'volume_ja_vendido': 2171.3813},
    {'cnpj': '057.349.409-68', 'propriedade': 'Pedreira', 'especie': 'Pinus taeda', 'volume_ja_vendido': 1492.09},
    {'cnpj': '057.349.409-68', 'propriedade': 'Santa Cruz do Rio Claro', 'especie': 'Pinus taeda', 'volume_ja_vendido': 21197.2548},
    {'cnpj': '057.349.409-68', 'propriedade': 'Sítio Vidal', 'especie': 'Pinus taeda', 'volume_ja_vendido': 4334.892},
    {'cnpj': '057.349.409-68', 'propriedade': 'Tigre', 'especie': 'Pinus taeda', 'volume_ja_vendido': 1137.845},
    {'cnpj': '51.679.608/0001-25', 'propriedade': 'Cacumbangue', 'especie': 'Pinus taeda', 'volume_ja_vendido': 249.87},
    {'cnpj': '51.679.608/0001-25', 'propriedade': 'Cacumbangue', 'especie': 'Eucalyptus grandis', 'volume_ja_vendido': 97.4},
    {'cnpj': '51.679.608/0001-25', 'propriedade': 'Santo Agostinho', 'especie': 'Pinus taeda', 'volume_ja_vendido': 23039.84},
    {'cnpj': '44.577.869/0002-50', 'propriedade': 'Araújo', 'especie': 'Pinus taeda', 'volume_ja_vendido': 39187.59},
    {'cnpj': '44.577.869/0002-50', 'propriedade': 'Araújo', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 1854.9},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Santa Cruz', 'especie': 'Pinus taeda', 'volume_ja_vendido': 58761.43},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Serro So I e II', 'especie': 'Pinus taeda', 'volume_ja_vendido': 563.91},
    {'cnpj': '29.116.865/0001-08', 'propriedade': 'Serro So III', 'especie': 'Pinus taeda', 'volume_ja_vendido': 696.67},
    {'cnpj': '81.490.500/0001-50', 'propriedade': 'Envolvido', 'especie': 'Eucalyptus sp', 'volume_ja_vendido': 182.49},
    {'cnpj': '81.490.500/0001-50', 'propriedade': 'Linha Borges', 'especie': 'Pinus taeda', 'volume_ja_vendido': 4620.02},
    {'cnpj': '81.490.500/0001-50', 'propriedade': 'Santa Lucia', 'especie': 'Pinus taeda', 'volume_ja_vendido': 2406.83},
]

def aplicar_ajustes_historicos(apps, schema_editor):
    """Registra como 'saída' o volume que já havia sido vendido antes da
    adoção do sistema, para que o saldo disponível reflita a realidade
    (Volume Certificado - Saldo informado na planilha de controle)."""
    Participant = apps.get_model('participants', 'Participant')
    Propriedade = apps.get_model('manejo', 'Propriedade')
    Especie = apps.get_model('manejo', 'Especie')
    InventarioEntrada = apps.get_model('manejo', 'InventarioEntrada')
    SaidaManejo = apps.get_model('manejo', 'SaidaManejo')

    hoje = date.today()
    aplicados = 0
    ignorados_sem_match = 0
    ignorados_ja_existe = 0

    for item in AJUSTES_HISTORICOS:
        participant = Participant.objects.filter(cnpj=item['cnpj']).first()
        if not participant:
            ignorados_sem_match += 1
            continue

        propriedade = Propriedade.objects.filter(
            participant=participant, nome=item['propriedade']
        ).first()
        especie = Especie.objects.filter(
            participant=participant, nome=item['especie']
        ).first()
        if not propriedade or not especie:
            ignorados_sem_match += 1
            continue

        entrada = InventarioEntrada.objects.filter(
            propriedade=propriedade, especie=especie
        ).first()
        if not entrada:
            ignorados_sem_match += 1
            continue

        ja_existe = SaidaManejo.objects.filter(
            entrada=entrada, documento='AJUSTE-HISTORICO'
        ).exists()
        if ja_existe:
            ignorados_ja_existe += 1
            continue

        SaidaManejo.objects.create(
            participant=participant,
            entrada=entrada,
            data=hoje,
            documento='AJUSTE-HISTORICO',
            cliente_nome='Vendas históricas (antes do sistema)',
            declaracao_fsc=True,
            volume=item['volume_ja_vendido'],
            unidade='m3',
            volume_m3=item['volume_ja_vendido'],
            observacoes=(
                'Ajuste de saldo: volume já vendido antes da adoção do sistema, '
                'calculado como Volume Certificado menos Saldo informado na planilha '
                'de controle original. Não representa uma venda individual real.'
            ),
        )
        aplicados += 1

    print(f"\n[Manejo FM] Ajustes históricos aplicados: {aplicados}")
    print(f"[Manejo FM] Ignorados (sem match propriedade/espécie): {ignorados_sem_match}")
    print(f"[Manejo FM] Ignorados (já existia ajuste): {ignorados_ja_existe}")


class Migration(migrations.Migration):

    dependencies = [
        ('manejo', '0003_bootstrap_propriedades_fm'),
    ]

    operations = [
        migrations.RunPython(aplicar_ajustes_historicos, migrations.RunPython.noop),
    ]
