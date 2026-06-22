from django.db import migrations
from datetime import date


MEMBROS_FM = [
    {
        'membro': '3 IRMÃOS FLORESTAL LTDA',
        'cnpj': '53.774.101/0001-86',
        'propriedades': [
            {'nome': 'Osmir Dalgallo', 'municipio': 'Bituruna', 'uf': 'PR', 'area': 114.18, 'especies': []},
            {'nome': 'São Pedro', 'municipio': 'General Carneiro', 'uf': 'PR', 'area': 228.19, 'especies': []},
            {'nome': 'Campo Alto Randa', 'municipio': 'Matos Costa', 'uf': 'SC', 'area': 375.34, 'especies': []},
            {'nome': 'Mato Novo', 'municipio': 'Bituruna', 'uf': 'PR', 'area': 50.28, 'especies': []},
            {'nome': 'Mato Queimado', 'municipio': 'Bituruna', 'uf': 'PR', 'area': 183.6, 'especies': []},
        ],
    },
    {
        'membro': 'ADEMILSON PIRES - COMERCIO E TRANSPORTE LTDA',
        'cnpj': '30.655.340/0001-11',
        'propriedades': [
            {'nome': 'Rancho Alegre', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 1817.06, 'especies': [['Pinus taeda', 113331.54]]},
            {'nome': 'Rio do Salto', 'municipio': 'Palmeira', 'uf': 'PR', 'area': 948.79, 'especies': [['Pinus taeda', 19782.61]]},
            {'nome': 'Chácara Charavara', 'municipio': 'Irati', 'uf': 'PR', 'area': 26.63, 'especies': [['Eucalyptus sp', 6485.52]]},
            {'nome': 'Cambiju', 'municipio': 'Ponta Grossa', 'uf': 'PR', 'area': 308.56, 'especies': []},
        ],
    },
    {
        'membro': 'AERC PARTICIPAÇÕES LTDA',
        'cnpj': '23.484.679/0001-37',
        'propriedades': [
            {'nome': 'Capão do Tigre', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 384.52, 'especies': [['Pinus taeda', 61792.995]]},
            {'nome': 'Butiá', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 48.62, 'especies': [['Eucalyptus sp', 563.76], ['Pinus taeda', 7940.07]]},
        ],
    },
    {
        'membro': 'AGRO FLORESTAL RIBEIRÃO DO MARQUÊS',
        'cnpj': 'PENDENTE-001',
        'propriedades': [
            {'nome': 'Gleba Marquês', 'municipio': 'Tunas do Paraná', 'uf': 'PR', 'area': 549.49, 'especies': [['Pinus elliottii', 227733.0]]},
        ],
    },
    {
        'membro': 'AGZ FOREST LTDA',
        'cnpj': 'PENDENTE-002',
        'propriedades': [
            {'nome': 'Limeira', 'municipio': 'Pinhão', 'uf': 'PR', 'area': 1332.92, 'especies': []},
            {'nome': 'São Pedro', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 44.52, 'especies': []},
        ],
    },
    {
        'membro': 'ALBERTO GOMES MARTINS',
        'cnpj': 'PENDENTE-003',
        'propriedades': [
            {'nome': 'Camargo', 'municipio': 'Reserva', 'uf': 'PR', 'area': 204.6, 'especies': [['Eucalyptus sp', 23346.0], ['Pinus taeda', 43069.27]]},
        ],
    },
    {
        'membro': 'ALIANÇA COMÉRCIO DE MADEIRAS LTDA',
        'cnpj': '33.285.403/0001-83',
        'propriedades': [
            {'nome': 'Xadrez', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 1141.9, 'especies': [['Pinus taeda', 282944.77]]},
        ],
    },
    {
        'membro': 'ANGELA DARIN DIAS',
        'cnpj': '29.116.865/0001-08',
        'propriedades': [
            {'nome': 'Lageado de Cima', 'municipio': 'Mallet', 'uf': 'PR', 'area': 125.99, 'especies': [['Pinus taeda', 16539.31]]},
            {'nome': 'Nova II', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 21.72, 'especies': [['Pinus taeda', 16698.09]]},
            {'nome': 'Santa Angela', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 279.02, 'especies': [['Pinus taeda', 49783.77]]},
            {'nome': 'Santa Helena', 'municipio': 'União da Vitória', 'uf': 'PR', 'area': 123.8, 'especies': [['Pinus taeda', 11062.15]]},
            {'nome': 'Vicinal 11', 'municipio': 'Mallet', 'uf': 'PR', 'area': 24.88, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'Vicinal 7-II', 'municipio': 'Mallet', 'uf': 'PR', 'area': 52.63, 'especies': [['Pinus taeda', 4005.73]]},
            {'nome': 'Vicinal 9', 'municipio': 'Mallet', 'uf': 'PR', 'area': 21.26, 'especies': [['Pinus taeda', 1050.71]]},
        ],
    },
    {
        'membro': 'A.T. COMÉRCIO E TRANSPORTES DE MADEIRAS LTDA',
        'cnpj': '00.883.416/0001-03',
        'propriedades': [
            {'nome': 'Paraíso', 'municipio': 'Bocaiuva do Sul', 'uf': 'PR', 'area': 156.02, 'especies': [['Pinus sp', 30000.0], ['Eucalyptus sp', 27000.0]]},
        ],
    },
    {
        'membro': 'BRASNILE INDUSTRIAL LTDA',
        'cnpj': '78.549.615/0001-69',
        'propriedades': [
            {'nome': 'Rio Bonito', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 62.41, 'especies': [['Eucalyptus dunnii', 12120.58]]},
            {'nome': 'Rio Vermelho', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 106.9, 'especies': [['Pinus taeda', 22688.76], ['Eucalyptus dunnii', 22375.7]]},
            {'nome': 'Sossego', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 42.84, 'especies': [['Pinus taeda', 17760.13]]},
            {'nome': 'Sossego I e II', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 28.31, 'especies': [['Pinus taeda', 7820.49], ['Eucalyptus dunnii', 4245.94]]},
            {'nome': 'Sossego III', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 6.53, 'especies': [['Eucalyptus dunnii', 2285.54]]},
            {'nome': 'Taquarizal', 'municipio': 'Irineópolis', 'uf': 'SC', 'area': 97.97, 'especies': [['Pinus taeda', 13193.48]]},
        ],
    },
    {
        'membro': 'BRUNO REINHOFER',
        'cnpj': 'PENDENTE-004',
        'propriedades': [
            {'nome': 'Santa Isabel', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 574.02, 'especies': [['Pinus taeda', 145129.02]]},
        ],
    },
    {
        'membro': 'CARAÚNO MADEIRAS LTDA',
        'cnpj': '02.058.184/0001-76',
        'propriedades': [
            {'nome': 'Caraúno', 'municipio': 'Bom Jesus', 'uf': 'RS', 'area': 2187.51, 'especies': [['Pinus taeda', 893396.8]]},
            {'nome': 'Morro Grande', 'municipio': 'São Francisco de Paula', 'uf': 'RS', 'area': 756.67, 'especies': [['Pinus taeda', 228069.46]]},
            {'nome': 'Rondinha', 'municipio': 'Bom Jesus', 'uf': 'RS', 'area': 1028.22, 'especies': [['Pinus taeda', 389752.49]]},
        ],
    },
    {
        'membro': 'CARLOS KRACIK ROSA',
        'cnpj': '003.960.019-04',
        'propriedades': [
            {'nome': 'Adriana II', 'municipio': 'Campo Belo do Sul', 'uf': 'SC', 'area': 67.24, 'especies': [['Pinus taeda', 45473.4]]},
        ],
    },
    {
        'membro': 'CLEITON KIELSE BORDINI CRISÓSTOMO',
        'cnpj': 'PENDENTE-005',
        'propriedades': [
            {'nome': 'Legacy', 'municipio': 'Campina Grande do Sul', 'uf': 'PR', 'area': 145.46, 'especies': []},
        ],
    },
    {
        'membro': 'COMBIO ENERGIA S/A',
        'cnpj': 'PENDENTE-006',
        'propriedades': [
            {'nome': 'Alvamar', 'municipio': 'Piedade', 'uf': 'SP', 'area': 623.08, 'especies': [['Eucalyptus sp', 40827.36]]},
            {'nome': 'Jogil', 'municipio': 'Natividade da Serra', 'uf': 'SP', 'area': 2101.94, 'especies': [['Eucalyptus sp', 81590.4]]},
            {'nome': 'Bom Jesus', 'municipio': 'Santa Bárbara do Oeste', 'uf': 'SP', 'area': 1220.32, 'especies': []},
            {'nome': 'Campo Formoso', 'municipio': 'Santa Bárbara do Oeste', 'uf': 'SP', 'area': 45.24, 'especies': []},
            {'nome': 'Morro Grande', 'municipio': 'Piracicaba', 'uf': 'SP', 'area': 44.35, 'especies': []},
            {'nome': 'Pacaembu', 'municipio': 'Monte Mor', 'uf': 'SP', 'area': 73.12, 'especies': []},
            {'nome': 'Santa Alice', 'municipio': 'Capivari', 'uf': 'SP', 'area': 401.14, 'especies': []},
            {'nome': 'Soma', 'municipio': 'Anhembi', 'uf': 'SP', 'area': 618.85, 'especies': []},
        ],
    },
    {
        'membro': 'COMPENSADOS FUCK LTDA',
        'cnpj': 'PENDENTE-007',
        'propriedades': [
            {'nome': 'Tamanduá', 'municipio': 'Canoinhas', 'uf': 'SC', 'area': 2730.66, 'especies': [['Pinus taeda', 173054.0], ['Eucalyptus sp', 42454.0]]},
        ],
    },
    {
        'membro': 'COMPENSADOS NOVO MILENIO LTDA',
        'cnpj': 'PENDENTE-008',
        'propriedades': [
            {'nome': 'São Roque', 'municipio': 'Flor da Serra do Sul', 'uf': 'PR', 'area': 143.78, 'especies': []},
        ],
    },
    {
        'membro': 'COMPENSADOS RELVAPLAC LTDA',
        'cnpj': '00.060.274/0001-76',
        'propriedades': [
            {'nome': 'Santa Joana', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 1158.3, 'especies': [['Pinus taeda', 86408.91], ['Eucalyptus dunnii', 7009.23]]},
        ],
    },
    {
        'membro': 'LEONIR ANTONIO BROCH',
        'cnpj': 'PENDENTE-023',
        'propriedades': [
            {'nome': 'Dona Clara', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 166.54, 'especies': []},
            {'nome': 'Santa Catarina', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 624.71, 'especies': []},
        ],
    },
    {
        'membro': 'COOPERATIVA FLORESTAL DOS CAMPOS GERAIS',
        'cnpj': '20.281.367/0001-38',
        'propriedades': [
            {'nome': 'Gurupiá', 'municipio': 'Reserva', 'uf': 'PR', 'area': 258.38, 'especies': [['Eucalyptus urograndis', 44925.0], ['Eucalyptus urograndis', 44925.0]]},
            {'nome': 'Shalon 10', 'municipio': 'Imbaú', 'uf': 'PR', 'area': 32.83, 'especies': [['Eucalyptus grandis', 6048.0]]},
        ],
    },
    {
        'membro': 'CRISTO REI FOREST MAD LTDA',
        'cnpj': '32.683.777/0003-56',
        'propriedades': [
            {'nome': 'Tacaniça', 'municipio': 'Itaperuçu', 'uf': 'PR', 'area': 188.61, 'especies': [['Pinus taeda', 69310.63]]},
        ],
    },
    {
        'membro': 'DANILO RAFAEL ALVES FERREIRA LTDA',
        'cnpj': 'PENDENTE-009',
        'propriedades': [
            {'nome': 'Água Branca', 'municipio': 'Castro', 'uf': 'PR', 'area': 185.8, 'especies': [['Pinus taeda', 37001.0]]},
            {'nome': 'Ribeirão das Areias 1', 'municipio': 'Castro', 'uf': 'PR', 'area': 184.14, 'especies': [['Pinus sp', 33297.0]]},
        ],
    },
    {
        'membro': 'ITAMAD TRANSPORTE E COMÉRCIO DE MADEIRAS LTDA',
        'cnpj': '29.271.176/0001-60',
        'propriedades': [
            {'nome': 'Herval 5', 'municipio': 'Castro', 'uf': 'PR', 'area': 709.41, 'especies': [['Pinus taeda', 25933.0]]},
            {'nome': 'Herval 6', 'municipio': 'Castro', 'uf': 'PR', 'area': 407.85, 'especies': [['Pinus taeda', 65477.0]]},
            {'nome': 'Ribeirão das Areias 4', 'municipio': 'Castro', 'uf': 'PR', 'area': 286.69, 'especies': [['Pinus taeda', 86224.0]]},
            {'nome': 'Ribeirãozinho', 'municipio': 'Castro', 'uf': 'PR', 'area': 167.77, 'especies': [['Pinus taeda', 8016.0]]},
        ],
    },
    {
        'membro': 'DIVOL COMÉRCIO DE MADEIRAS E TRANSPORTES LTDA',
        'cnpj': '35.158.618/0001-69',
        'propriedades': [
            {'nome': 'Campos Verdes Unidos', 'municipio': 'Buri', 'uf': 'SP', 'area': 196.52, 'especies': [['Pinus elliottii', 15372.24], ['Pinus caribeae var. hondurensis', 5703.08]]},
            {'nome': 'Rio Claro', 'municipio': 'Barra do Chapéu', 'uf': 'SP', 'area': 120.82, 'especies': []},
            {'nome': 'Vilas Boas', 'municipio': 'Bom Sucesso de Itararé', 'uf': 'SP', 'area': 65.96, 'especies': []},
        ],
    },
    {
        'membro': 'EDUARDO MONTEIRO DE VALÕES',
        'cnpj': 'PENDENTE-010',
        'propriedades': [
            {'nome': 'Santana', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 223.66, 'especies': [['Eucalyptus sp', 64280.0]]},
        ],
    },
    {
        'membro': 'ERMANO VARASCHIN JUNIOR',
        'cnpj': '437.660.480-15',
        'propriedades': [
            {'nome': 'Alegrete', 'municipio': 'Lapa', 'uf': 'PR', 'area': 412.85, 'especies': [['Pinus taeda', 22001.62]]},
        ],
    },
    {
        'membro': 'ESTRELA AGROFLORESTAL LTDA',
        'cnpj': '79.441.168/0001-92',
        'propriedades': [
            {'nome': 'Alegria', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 535.63, 'especies': [['Pinus taeda', 46365.79]]},
            {'nome': 'Bom Sucesso A', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 302.51, 'especies': [['Pinus taeda', 34025.2]]},
            {'nome': 'Do Salto', 'municipio': 'Palmas', 'uf': 'PR', 'area': 156.57, 'especies': [['Pinus taeda', 63188.97]]},
            {'nome': 'Santa Clara', 'municipio': 'Palmas', 'uf': 'PR', 'area': 393.88, 'especies': [['Pinus taeda', 194146.73]]},
            {'nome': 'Santa Clara D', 'municipio': 'Palmas', 'uf': 'PR', 'area': 193.14, 'especies': [['Pinus taeda', 89119.8]]},
            {'nome': 'Santa Tereza', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 1140.71, 'especies': [['Pinus taeda', 201403.21], ['Eucalyptus sp', 5027.74]]},
            {'nome': 'Santana do Pitanga', 'municipio': 'Palmas', 'uf': 'PR', 'area': 458.39, 'especies': [['Pinus taeda', 162082.45]]},
            {'nome': 'Cabanha São Rafael', 'municipio': 'Honório Serpa', 'uf': 'PR', 'area': 169.86, 'especies': [['Pinus taeda', 58035.38]]},
            {'nome': 'Cruzeiro I', 'municipio': 'Palmas', 'uf': 'PR', 'area': 233.78, 'especies': []},
        ],
    },
    {
        'membro': 'EUGENIA PODOLAN LACERDA VIEIRA',
        'cnpj': 'PENDENTE-011',
        'propriedades': [
            {'nome': 'Araras', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 220.12, 'especies': []},
            {'nome': 'Baú', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 106.82, 'especies': []},
            {'nome': 'Capão Alto', 'municipio': 'Candói', 'uf': 'PR', 'area': 19.61, 'especies': []},
            {'nome': 'Faxinal das Araras', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 361.32, 'especies': []},
            {'nome': 'Palmeira', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 59.72, 'especies': []},
            {'nome': 'Serro Verde', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 24.5, 'especies': []},
            {'nome': 'Tunas e Tuninhas', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 1015.65, 'especies': []},
            {'nome': 'Vividence', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 6.28, 'especies': []},
        ],
    },
    {
        'membro': 'FAGANELLO INDÚSTRIA DE COMPENSADOS EIRELI',
        'cnpj': '08.248.364/0001-05',
        'propriedades': [
            {'nome': 'Boa Vista', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 152.02, 'especies': [['Pinus taeda', 45749.0]]},
            {'nome': 'Vitor Weber', 'municipio': 'Canoinhas', 'uf': 'SC', 'area': 49.85, 'especies': [['Pinus taeda', 15880.0]]},
        ],
    },
    {
        'membro': 'FAPOLPA AGRO FLORESTAL LTDA',
        'cnpj': 'PENDENTE-012',
        'propriedades': [
            {'nome': 'Curucaca', 'municipio': 'Honório Serpa', 'uf': 'PR', 'area': 76.19, 'especies': [['Pinus taeda', 24191.8]]},
            {'nome': 'Bom Sucesso B', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 182.09, 'especies': [['Pinus taeda', 34025.2]]},
            {'nome': 'São Pedro', 'municipio': 'Mangueirinha', 'uf': 'PR', 'area': 152.72, 'especies': [['Pinus taeda', 30985.89], ['Eucalyptus sp', 10519.74]]},
        ],
    },
    {
        'membro': 'FAZENDA PASTORE LTDA',
        'cnpj': 'PENDENTE-013',
        'propriedades': [
            {'nome': 'Boa Vista', 'municipio': 'Palmas', 'uf': 'PR', 'area': 420.98, 'especies': []},
            {'nome': 'Das Pedras', 'municipio': 'Palmas', 'uf': 'PR', 'area': 463.8, 'especies': [['Pinus sp', 62939.7]]},
            {'nome': 'Fazenda Nossa Senhora da Luz', 'municipio': 'Palmas', 'uf': 'PR', 'area': 69.52, 'especies': []},
        ],
    },
    {
        'membro': 'FLONA IRATI FLORESTAL LTDA',
        'cnpj': '54.964.725/0001-29',
        'propriedades': [
            {'nome': 'Flona de Irati', 'municipio': 'Fernandes Pinheiro', 'uf': 'PR', 'area': 2362.19, 'especies': [['Pinus taeda', 673688.0]]},
        ],
    },
    {
        'membro': 'FLORA AGRONEGÓCIOS LTDA',
        'cnpj': '14.792.934/0001-18',
        'propriedades': [
            {'nome': 'ABC', 'municipio': 'Pedro Canário', 'uf': 'ES', 'area': 1239.88, 'especies': [['Eucalyptus', 174974.0]]},
            {'nome': 'Aliança', 'municipio': 'Montanha', 'uf': 'ES', 'area': 1143.96, 'especies': [['Eucalyptus', 132300.0]]},
            {'nome': 'Céu Azul', 'municipio': 'Mucuri', 'uf': 'BA', 'area': 142.26, 'especies': [['Eucalyptus', 0.0]]},
            {'nome': 'Gabiroba', 'municipio': 'Ibirapuã', 'uf': 'BA', 'area': 57.2, 'especies': [['Eucalyptus', 0.0]]},
            {'nome': 'São João', 'municipio': 'Mucuri', 'uf': 'BA', 'area': 195.21, 'especies': [['Eucalyptus', 0.0]]},
        ],
    },
    {
        'membro': 'FLORESTAL PIRÂMIDE LTDA',
        'cnpj': 'PENDENTE-014',
        'propriedades': [
            {'nome': 'Campo Alto', 'municipio': 'Santa Cecília', 'uf': 'SC', 'area': 99.49, 'especies': []},
        ],
    },
    {
        'membro': 'FORMASA AGROFLORESTAL LTDA',
        'cnpj': '06.325.423/0001-68',
        'propriedades': [
            {'nome': 'Lagiadinho', 'municipio': 'Monte Castelo', 'uf': 'SC', 'area': 170.62, 'especies': []},
            {'nome': 'Residência Fuck', 'municipio': 'Monte Castelo', 'uf': 'SC', 'area': 1551.36, 'especies': [['Pinus taeda', 83571.0]]},
        ],
    },
    {
        'membro': 'FRÍSIA COOPERATIVA AGROINDUSTRIAL',
        'cnpj': '76.107.770/0019-29',
        'propriedades': [
            {'nome': 'Vale do Jotuva XI', 'municipio': 'Carambeí', 'uf': 'PR', 'area': 58.31, 'especies': [['Eucalyptus sp', 9973.3]]},
            {'nome': 'São Paulo', 'municipio': 'Castro', 'uf': 'PR', 'area': 530.56, 'especies': [['Pinus taeda', 6465.14]]},
            {'nome': 'Tapera', 'municipio': 'Ponta Grossa', 'uf': 'PR', 'area': 68.13, 'especies': [['Eucalyptus sp', 7492.22]]},
            {'nome': 'Gaiofatto', 'municipio': 'Ivaí', 'uf': 'PR', 'area': 31.03, 'especies': []},
            {'nome': 'João de Barro', 'municipio': 'Ivaí', 'uf': 'PR', 'area': 12.06, 'especies': []},
            {'nome': 'Sabão', 'municipio': 'Carambeí', 'uf': 'PR', 'area': 165.64, 'especies': []},
        ],
    },
    {
        'membro': 'FV DE ARAUJO S/A MADEIRAS, AGRICULTURA, INDUSTRIA e COMERCIO',
        'cnpj': 'PENDENTE-015',
        'propriedades': [
            {'nome': 'Meio', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 56.01, 'especies': []},
            {'nome': 'Nico', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 80.09, 'especies': []},
            {'nome': 'Paineira', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 584.91, 'especies': []},
            {'nome': 'São Francisco', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 1045.6, 'especies': []},
            {'nome': 'São João', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 507.52, 'especies': []},
            {'nome': 'São Pedro', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 1101.25, 'especies': []},
        ],
    },
    {
        'membro': 'GEANE JORGE PASSAÚRA',
        'cnpj': 'PENDENTE-016',
        'propriedades': [
            {'nome': 'Niasi', 'municipio': 'Jaguariaiva', 'uf': 'PR', 'area': 98.57, 'especies': [['Pinus taeda', 16604.5]]},
        ],
    },
    {
        'membro': 'GUMERCINDO BARPP',
        'cnpj': 'PENDENTE-017',
        'propriedades': [
            {'nome': 'Rio Bonito I', 'municipio': 'Lebon Régis', 'uf': 'SC', 'area': 567.59, 'especies': [['Pinus taeda', 171735.26]]},
        ],
    },
    {
        'membro': 'HORÁCIO UEQUE',
        'cnpj': 'PENDENTE-018',
        'propriedades': [
            {'nome': 'Ozório de Almeida Taques', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 367.16, 'especies': []},
        ],
    },
    {
        'membro': 'INDUSTRIA DE COMPENSADOS GUARARAPES',
        'cnpj': 'PENDENTE-019',
        'propriedades': [
            {'nome': 'Invernadinha', 'municipio': 'São Joaquim', 'uf': 'SC', 'area': 502.03, 'especies': [['Pinus sp', 249310.02]]},
            {'nome': 'São Roque', 'municipio': 'Passos Maia', 'uf': 'SC', 'area': 196.03, 'especies': [['Pinus taeda', 124963.3921]]},
            {'nome': 'Centro 1', 'municipio': 'Ibicaré', 'uf': 'SC', 'area': 52.77, 'especies': []},
            {'nome': 'Colônia Muller', 'municipio': 'Pinheiro Preto', 'uf': 'SC', 'area': 90.37, 'especies': []},
            {'nome': 'Duque 3', 'municipio': 'Ibicaré', 'uf': 'SC', 'area': 14.13, 'especies': []},
            {'nome': 'Estrela', 'municipio': 'Ibicaré', 'uf': 'SC', 'area': 94.62, 'especies': []},
            {'nome': 'Linha Duque de Caxias', 'municipio': 'Ibicaré', 'uf': 'SC', 'area': 85.32, 'especies': []},
        ],
    },
    {
        'membro': 'INDUSTRIA DE COMPENSADOS SUDATI',
        'cnpj': '76.107.770/0019-29',
        'propriedades': [
            {'nome': 'Califórnia', 'municipio': 'Ribeirão do Pinhal', 'uf': 'PR', 'area': 2011.58, 'especies': [['Eucalyptus sp', 363653.03]]},
            {'nome': 'Covósinho', 'municipio': 'Mangueirinha', 'uf': 'PR', 'area': 697.47, 'especies': [['Pinus sp', 196245.45]]},
            {'nome': 'Porta do Céu', 'municipio': 'Reserva', 'uf': 'PR', 'area': 949.01, 'especies': [['Eucalyptus urograndis', 61788.601]]},
            {'nome': 'São José do Faxinal', 'municipio': 'Arapoti', 'uf': 'PR', 'area': 82.28, 'especies': [['Eucalyptus urograndis', 32631.5169], ['Pinus taeda', 8112.62]]},
            {'nome': 'São Pedro', 'municipio': 'Palmas', 'uf': 'PR', 'area': 112.65, 'especies': [['Pinus taeda', 49559.5]]},
            {'nome': 'São Roque', 'municipio': 'Passos Maia', 'uf': 'SC', 'area': 170.0, 'especies': []},
            {'nome': 'Barra Grande', 'municipio': 'Tomazina', 'uf': 'PR', 'area': 966.83, 'especies': []},
        ],
    },
    {
        'membro': 'INDUSTRIAL ARBHORES COMPENSADOS LTDA',
        'cnpj': '10.887.398/0001-83',
        'propriedades': [
            {'nome': 'São Bento', 'municipio': 'General Carneiro', 'uf': 'PR', 'area': 431.83, 'especies': [['Pinus taeda', 38864.1]]},
        ],
    },
    {
        'membro': 'ITAMARATI INDUSTRIA DE COMPENSADOS LTDA',
        'cnpj': '00.149.821/0001-94',
        'propriedades': [
            {'nome': 'Austria', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 154.08, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'Santo Expedito', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 102.76, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'São João da Ronda', 'municipio': 'Mangueirinha', 'uf': 'PR', 'area': 114.12, 'especies': [['Pinus elliottii', 36231.31], ['Eucalyptus dunnii', 7496.49]]},
            {'nome': 'São Joaquim', 'municipio': 'General Carneiro', 'uf': 'PR', 'area': 387.11, 'especies': [['Pinus elliottii', 46936.19], ['Eucalyptus dunnii', 6856.1]]},
        ],
    },
    {
        'membro': 'JAQUIRANA MADEIRAS LTDA',
        'cnpj': '53.548.361/0002-14',
        'propriedades': [
            {'nome': 'Rondinha', 'municipio': 'Bom Jesus', 'uf': 'RS', 'area': 468.63, 'especies': [['Pinus taeda', 45235.62]]},
            {'nome': 'Cadete', 'municipio': 'Lages', 'uf': 'SC', 'area': 1683.17, 'especies': []},
        ],
    },
    {
        'membro': 'JEAN RICARDO SCHARAN',
        'cnpj': 'PENDENTE-020',
        'propriedades': [
            {'nome': 'Scharan A', 'municipio': 'Prudentópolis', 'uf': 'PR', 'area': 59.81, 'especies': []},
        ],
    },
    {
        'membro': 'KAMYLLE BOBATO',
        'cnpj': 'PENDENTE-021',
        'propriedades': [
            {'nome': 'Santa Joana', 'municipio': 'Teixeira Soares', 'uf': 'PR', 'area': 1217.22, 'especies': [['Pinus sp', 52300.68]]},
        ],
    },
    {
        'membro': 'KOREVAR GESTÃO FLORESTAL LTDA',
        'cnpj': '58.867.099/0001-03',
        'propriedades': [
            {'nome': 'Cambiju', 'municipio': 'Ponta Grossa', 'uf': 'PR', 'area': 334.46, 'especies': []},
        ],
    },
    {
        'membro': 'LEONICIO LOPES DA CRUZ',
        'cnpj': 'PENDENTE-022',
        'propriedades': [
            {'nome': 'Santa Regina', 'municipio': 'Itapeva', 'uf': 'SP', 'area': 790.05, 'especies': []},
        ],
    },
    {
        'membro': 'LG MADEIRAS LTDA',
        'cnpj': '08.732.926/0001-83',
        'propriedades': [
            {'nome': 'Horongozo - Rio Saltinho', 'municipio': 'Chapadão do Lageado', 'uf': 'SC', 'area': 29.01, 'especies': [['Eucalyptus sp', 3630.19]]},
            {'nome': 'LG - Rio Engano', 'municipio': 'Alfredo Wagner', 'uf': 'SC', 'area': 9.94, 'especies': [['Eucalyptus sp', 4377.56]]},
            {'nome': 'Cristiano VR - Alto Molungu', 'municipio': 'Vidal Ramos', 'uf': 'SC', 'area': 71.89, 'especies': [['Pinus sp', 9910.76]]},
            {'nome': 'LG - Capitão Mohr', 'municipio': 'Bocaina do Sul', 'uf': 'SC', 'area': 90.31, 'especies': [['Pinus sp', 19227.2]]},
            {'nome': 'Francisco Velter', 'municipio': 'Ituporanga', 'uf': 'SC', 'area': 23.89, 'especies': []},
            {'nome': 'Heriberto Muller', 'municipio': 'Chapadão do Lageado', 'uf': 'SC', 'area': 26.32, 'especies': []},
            {'nome': 'Juliano Petersen', 'municipio': 'Petrolândia', 'uf': 'SC', 'area': 22.5, 'especies': []},
            {'nome': 'Nasori Catuira', 'municipio': 'Alfredo Wagner', 'uf': 'SC', 'area': 41.66, 'especies': []},
            {'nome': 'Vanderson Eger', 'municipio': 'Petrolândia', 'uf': 'SC', 'area': 7.65, 'especies': []},
        ],
    },
    {
        'membro': 'LINHA ATUAL INDÚSTRIA E COMERCIO DE MADEIRAS LTDA',
        'cnpj': '01.099.739/0005-99',
        'propriedades': [
            {'nome': 'Brilhante XX', 'municipio': 'Ilhota', 'uf': 'SC', 'area': 235.95, 'especies': [['Pinus sp', 6283.82]]},
            {'nome': 'Laranjeiras', 'municipio': 'Luiz Alves', 'uf': 'SC', 'area': 389.65, 'especies': [['Eucalyptus urograndis', 36070.19]]},
            {'nome': 'Morro Grande & Lagoa', 'municipio': 'Ilhota', 'uf': 'SC', 'area': 545.96, 'especies': [['Pinus sp', 53707.5533]]},
            {'nome': 'Pratinha', 'municipio': 'Itajaí', 'uf': 'SC', 'area': 166.63, 'especies': []},
        ],
    },
    {
        'membro': 'LUCAS ROVEDA GUBERT',
        'cnpj': '007.368.319-16',
        'propriedades': [
            {'nome': 'Cachoeira Branca', 'municipio': 'Prudentópolis', 'uf': 'PR', 'area': 301.29, 'especies': [['Pinus taeda', 167.48], ['Eucalyptus sp', 32064.13]]},
            {'nome': 'Rio Bonito', 'municipio': 'Prudentópolis', 'uf': 'PR', 'area': 306.84, 'especies': [['Pinus taeda', 2096.19], ['Eucalyptus sp', 49477.07]]},
            {'nome': 'Sítio Rio Bonito', 'municipio': 'Prudentópolis', 'uf': 'PR', 'area': 33.03, 'especies': [['Eucalyptus sp', 886.32]]},
        ],
    },
    {
        'membro': 'LUIS CARLOS VATRIN',
        'cnpj': 'PENDENTE-024',
        'propriedades': [
            {'nome': 'Santa Luzia', 'municipio': 'Reserva do Iguaçu', 'uf': 'PR', 'area': 224.6, 'especies': [['Pinus taeda', 32038.31], ['Eucalyptus sp', 25000.0]]},
        ],
    },
    {
        'membro': 'LUIZ FELIPE AREOVALDO CALHIM MANOEL ABUD',
        'cnpj': '08.396.358/0007-82',
        'propriedades': [
            {'nome': 'Fazenda Nova Piracicaba', 'municipio': 'Itapeva', 'uf': 'SP', 'area': 347.33, 'especies': [['Pinus elliottii', 612.0]]},
            {'nome': 'Fazenda São Petrônio', 'municipio': 'Itapeva', 'uf': 'SP', 'area': 377.3, 'especies': [['Pinus elliottii', 1236.0]]},
        ],
    },
    {
        'membro': 'MBR TRANSPORTES E EXTRACÃO FLORESTAL LTDA',
        'cnpj': '34.113.986/0001-28',
        'propriedades': [
            {'nome': 'Cerrito II', 'municipio': 'São Francisco de Paula', 'uf': 'RS', 'area': 261.3, 'especies': []},
        ],
    },
    {
        'membro': 'M. GEYER E CIA LTDA',
        'cnpj': '34.446.573/0001-65',
        'propriedades': [
            {'nome': 'Geyer', 'municipio': 'Biturna', 'uf': 'PR', 'area': 4905.6, 'especies': [['Pinus sp', 248538.83]]},
            {'nome': 'Plínio', 'municipio': 'Biturna', 'uf': 'PR', 'area': 269.61, 'especies': []},
            {'nome': 'Papuã', 'municipio': 'Biturna', 'uf': 'PR', 'area': 320.99, 'especies': []},
        ],
    },
    {
        'membro': 'MADEIREIRA LOURO LTDA',
        'cnpj': '10.768.360/0001-91',
        'propriedades': [
            {'nome': 'Dorizon', 'municipio': 'Mallet', 'uf': 'PR', 'area': 87.31, 'especies': [['Pinus taeda', 8324.51]]},
            {'nome': 'Potinga', 'municipio': 'Mallet', 'uf': 'PR', 'area': 35.46, 'especies': [['Pinus taeda', 5758.52]]},
            {'nome': 'Vidal', 'municipio': 'Cruz Machado', 'uf': 'PR', 'area': 253.05, 'especies': [['Pinus taeda', 16620.74]]},
        ],
    },
    {
        'membro': 'MADEIREIRA RIO CLARO LTDA',
        'cnpj': '78.897.600/0002-72',
        'propriedades': [
            {'nome': 'Areia Branca', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 248.24, 'especies': [['Pinus sp', 22093.89]]},
            {'nome': 'Assay 01', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 11.93, 'especies': [['Eucalyptus urograndis', 6.4], ['Pinus sp', 3519.15]]},
            {'nome': 'Bandachaeski', 'municipio': 'Mallet', 'uf': 'PR', 'area': 8.33, 'especies': [['Pinus sp', 661.34]]},
            {'nome': 'Barra I', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 49.07, 'especies': [['Pinus sp', 17737.0]]},
            {'nome': 'Barra II', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 29.79, 'especies': [['Pinus sp', 12687.51]]},
            {'nome': 'Charqueada Paulista', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 23.46, 'especies': [['Pinus sp', 2800.0]]},
            {'nome': 'Choma', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 13.02, 'especies': [['Pinus sp', 3691.84]]},
            {'nome': 'Gabardo', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 10.34, 'especies': [['Pinus sp', 3336.74]]},
            {'nome': 'Guaviroval', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 26.14, 'especies': [['Pinus sp', 2463.58]]},
            {'nome': 'Jaremko', 'municipio': 'Paulo Frontin', 'uf': 'PR', 'area': 16.33, 'especies': [['Pinus sp', 1580.64]]},
            {'nome': 'Linha Oeste Duas', 'municipio': 'Mallet', 'uf': 'PR', 'area': 23.61, 'especies': [['Pinus sp', 0.0]]},
            {'nome': 'Nivaldo', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 18.2, 'especies': [['Pinus sp', 1085.0]]},
            {'nome': 'Paraná', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 18.6, 'especies': [['Pinus sp', 638.75]]},
            {'nome': 'Pinhalzinho', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 10.28, 'especies': [['Pinus sp', 1950.0]]},
            {'nome': 'Pontilhão', 'municipio': 'São Mateus do Sul', 'uf': 'PR', 'area': 326.13, 'especies': [['Pinus sp', 29040.16]]},
            {'nome': 'Riozinho de Baixo', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 28.56, 'especies': [['Pinus sp', 7798.61]]},
            {'nome': 'Ruppel', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 12.01, 'especies': [['Pinus sp', 850.0]]},
            {'nome': 'Serrinha I', 'municipio': 'Rio Azul', 'uf': 'PR', 'area': 7.19, 'especies': [['Pinus sp', 1576.81]]},
            {'nome': 'Stuski', 'municipio': 'São Mateus do Sul', 'uf': 'PR', 'area': 15.05, 'especies': [['Pinus sp', 4135.5737]]},
            {'nome': 'Zawadzki', 'municipio': 'Mallet', 'uf': 'PR', 'area': 117.03, 'especies': [['Pinus sp', 4967.11], ['Eucalyptus urograndis', 1800.0]]},
        ],
    },
    {
        'membro': 'MADPLUMA COMÉRCIO DE MADEIRAS LTDA',
        'cnpj': '12.442.230/0001-90',
        'propriedades': [
            {'nome': 'Ozório de Almeida Taques', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 367.16, 'especies': [['Pinus sp', 10947.01], ['Eucalyptus urograndis', 5479.29]]},
        ],
    },
    {
        'membro': 'MARCOS VINICIUS CHAGAS KAWAMURA',
        'cnpj': 'PENDENTE-025',
        'propriedades': [
            {'nome': 'Sítio Monjolinho', 'municipio': 'Nova Campina', 'uf': 'SP', 'area': 60.67, 'especies': [['Pinus sp', 6225.76]]},
            {'nome': 'Sítio Arapinus', 'municipio': 'Itapeva', 'uf': 'SP', 'area': 19.86, 'especies': [['Pinus sp', 10877.99]]},
        ],
    },
    {
        'membro': 'MARINI INDÚSTRIA DE COMPENSADOS LTDA',
        'cnpj': '05.552.102/0001-33',
        'propriedades': [
            {'nome': 'Faxinal', 'municipio': 'São Francisco de Paula', 'uf': 'RS', 'area': 819.71, 'especies': [['Eucalyptus sp', 25362.0], ['Pinus sp', 422858.0]]},
        ],
    },
    {
        'membro': 'MICHEL RICARDO JOCK',
        'cnpj': '390.083.632-91',
        'propriedades': [
            {'nome': 'Campina da Alegria', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 28.08, 'especies': [['Eucalyptus saligna', 8951.04]]},
            {'nome': 'Campina da Alegria 2', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 10.56, 'especies': []},
            {'nome': 'Sítio Cachoeirão', 'municipio': 'Imbaú', 'uf': 'PR', 'area': 47.3, 'especies': [['Eucalyptus grandis', 11072.82]]},
            {'nome': 'Sítio Cachoeirão 2', 'municipio': 'Imbaú', 'uf': 'PR', 'area': 19.57, 'especies': [['Eucalyptus grandis', 5923.47]]},
        ],
    },
    {
        'membro': 'MILLENIUM MADEIRAS LTDA',
        'cnpj': '10.319.233/0001-05',
        'propriedades': [
            {'nome': 'Martins', 'municipio': 'Reserva', 'uf': 'PR', 'area': 141.33, 'especies': [['Eucalyptus sp', 38647.0]]},
            {'nome': 'Socorro', 'municipio': 'Tibagi', 'uf': 'PR', 'area': 583.84, 'especies': [['Pinus sp', 80000.0]]},
            {'nome': 'Arroio Bonito', 'municipio': 'Reserva', 'uf': 'PR', 'area': 76.85, 'especies': [['Eucalyptus sp', 20766.0], ['Pinus sp', 7405.0]]},
            {'nome': 'Barreirinho', 'municipio': 'Reserva', 'uf': 'PR', 'area': 26.87, 'especies': []},
        ],
    },
    {
        'membro': 'MIRALUZ INDÚSTRIA E COMÉRCIO DE MADEIRAS LTDA',
        'cnpj': '75.596.106/0001-07',
        'propriedades': [
            {'nome': 'Cino Matão', 'municipio': 'Sengés', 'uf': 'PR', 'area': 63.8, 'especies': [['Pinus sp', 18407.0]]},
            {'nome': 'Santa Teresa', 'municipio': 'Sengés', 'uf': 'PR', 'area': 226.42, 'especies': [['Eucalyptus', 99678.0]]},
            {'nome': 'Formigas', 'municipio': 'Capão Bonito', 'uf': 'SP', 'area': 113.27, 'especies': [['Pinus sp', 37690.54]]},
            {'nome': 'Coimbra', 'municipio': 'Ribeirão Branco', 'uf': 'SP', 'area': 800.1, 'especies': [['Eucalyptus', 235351.13]]},
            {'nome': 'Santa Clara II', 'municipio': 'Ribeirão Branco', 'uf': 'SP', 'area': 358.26, 'especies': [['Eucalyptus', 158028.88]]},
            {'nome': 'Luso', 'municipio': 'Sengés', 'uf': 'PR', 'area': 85.63, 'especies': []},
        ],
    },
    {
        'membro': 'ML AGROPECUÁRIA LTDA',
        'cnpj': 'PENDENTE-026',
        'propriedades': [
            {'nome': 'Trieste', 'municipio': 'Água Doce', 'uf': 'SC', 'area': 562.92, 'especies': [['Pinus elliottii', 37938.96]]},
            {'nome': 'Santa Inês', 'municipio': 'Passos Maia', 'uf': 'SC', 'area': 658.96, 'especies': []},
            {'nome': 'São Vicente', 'municipio': 'Treze Tílias', 'uf': 'SC', 'area': 61.2, 'especies': []},
        ],
    },
    {
        'membro': 'MOACIR DE MELLO PORCIUNCULA',
        'cnpj': 'PENDENTE-027',
        'propriedades': [
            {'nome': 'Samoig', 'municipio': 'Roncador', 'uf': 'PR', 'area': 184.2, 'especies': []},
        ],
    },
    {
        'membro': 'NEWSTAR PARTICIPAÇÕES LTDA',
        'cnpj': '23.468.476/0001-57',
        'propriedades': [
            {'nome': 'Capão do Tigre', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 384.52, 'especies': [['Pinus taeda', 61792.995]]},
            {'nome': 'Butiá', 'municipio': 'São José dos Ausentes', 'uf': 'RS', 'area': 48.62, 'especies': [['Eucalyptus sp', 563.76], ['Pinus taeda', 7940.07]]},
        ],
    },
    {
        'membro': 'OLINTO PEDRO ZONIN',
        'cnpj': 'PENDENTE-028',
        'propriedades': [
            {'nome': 'Alegria III', 'municipio': 'Palmas', 'uf': 'PR', 'area': 224.13, 'especies': []},
        ],
    },
    {
        'membro': 'OTTO CLAUDIO JOCK',
        'cnpj': 'PENDENTE-029',
        'propriedades': [
            {'nome': 'Campina da Alegria', 'municipio': 'Reserva', 'uf': 'PR', 'area': 123.2, 'especies': [['Pinus taeda', 2738.39], ['Eucalyptus sp', 39357.89]]},
        ],
    },
    {
        'membro': 'OURO VERDE AGRONEGÓCIO',
        'cnpj': 'PENDENTE-030',
        'propriedades': [
            {'nome': 'Água Marinha I', 'municipio': 'Damianópolis', 'uf': 'GO', 'area': 582.55, 'especies': []},
            {'nome': 'Água Marinha II', 'municipio': 'Damianópolis', 'uf': 'GO', 'area': 144.43, 'especies': []},
        ],
    },
    {
        'membro': 'PALMASPLAC AGROPASTORIL LTDA',
        'cnpj': '74.058.710/0001-09',
        'propriedades': [
            {'nome': 'Alegria III', 'municipio': 'Palmas', 'uf': 'PR', 'area': 105.47, 'especies': [['Pinus sp', 45485.13]]},
            {'nome': 'Boa Vista', 'municipio': 'Palmas', 'uf': 'PR', 'area': 420.98, 'especies': [['Pinus sp', 60465.6]]},
            {'nome': 'Chopin II', 'municipio': 'Palmas', 'uf': 'PR', 'area': 487.72, 'especies': [['Pinus sp', 78974.0338]]},
            {'nome': 'Das Pedras', 'municipio': 'Palmas', 'uf': 'PR', 'area': 463.8, 'especies': [['Pinus sp', 62939.7]]},
            {'nome': 'Fazenda Nossa Senhora da Luz', 'municipio': 'Palmas', 'uf': 'PR', 'area': 69.52, 'especies': [['Pinus sp', 39702.0]]},
            {'nome': 'Fazenda Paiol Velho', 'municipio': 'General Carneiro', 'uf': 'PR', 'area': 730.69, 'especies': []},
        ],
    },
    {
        'membro': 'PASSAÚRA E FERNANDES AGRONEGÓCIOS S/A',
        'cnpj': 'PENDENTE-031',
        'propriedades': [
            {'nome': 'Niasi', 'municipio': 'Jaguariaiva', 'uf': 'PR', 'area': 49.29, 'especies': []},
        ],
    },
    {
        'membro': 'PLENOVALE FLORESTAL S/A',
        'cnpj': '75.157.974/0001-82',
        'propriedades': [
            {'nome': 'Domingão', 'municipio': 'Tunas do Paraná', 'uf': 'PR', 'area': 326.8, 'especies': [['Eucalyptus sp', 53614.0]]},
        ],
    },
    {
        'membro': 'R&S FLORESTAL LTDA',
        'cnpj': '08.349.614/0001-95',
        'propriedades': [
            {'nome': 'Cachoeira do Orvalho', 'municipio': 'Guapiara', 'uf': 'PR', 'area': 306.05, 'especies': [['Eucalyptus sp', 75080.0]]},
            {'nome': 'Funil', 'municipio': 'Morretes', 'uf': 'PR', 'area': 351.31, 'especies': [['Pinus taeda', 2330.0], ['Eucalyptus saligna', 440.9014], ['Eucalyptus urograndis', 25474.0]]},
        ],
    },
    {
        'membro': 'RANDA PORTAS, MOLDURAS E COMPENSADOS LTDA',
        'cnpj': 'PENDENTE-032',
        'propriedades': [
            {'nome': 'Campo Alto Arrendada', 'municipio': 'Matos Costa', 'uf': 'SC', 'area': 155.39, 'especies': []},
        ],
    },
    {
        'membro': 'RAS REFLORESTAMENTO LTDA',
        'cnpj': '43.446.111/0003-09',
        'propriedades': [
            {'nome': 'América do Sul', 'municipio': 'Nova Campina', 'uf': 'SP', 'area': 1202.5, 'especies': [['Eucalyptus urograndis', 13579.86], ['Pinus sp', 28727.46]]},
            {'nome': 'Fazenda Alto Vale', 'municipio': 'Apiaí', 'uf': 'SP', 'area': 33.64, 'especies': [['Pinus taeda', 8212.0]]},
            {'nome': 'Sítio Paraíso', 'municipio': 'Itapirapuã Paulista', 'uf': 'SP', 'area': 36.22, 'especies': [['Pinus taeda', 6258.0]]},
        ],
    },
    {
        'membro': 'RAVANELLO AGROPECUÁRIA LTDA',
        'cnpj': 'PENDENTE-033',
        'propriedades': [
            {'nome': 'Palmital - Quinhão I', 'municipio': 'União da Vitória', 'uf': 'PR', 'area': 678.6, 'especies': [['Eucalyptus dunnii', 9103.2234], ['Pinus taeda', 67538.78]]},
            {'nome': 'Palmital II', 'municipio': 'União da Vitória', 'uf': 'PR', 'area': 765.62, 'especies': [['Eucalyptus dunnii', 12708.0], ['Pinus taeda', 91429.0]]},
            {'nome': 'Serra da Esperança I', 'municipio': 'União da Vitória', 'uf': 'PR', 'area': 49.86, 'especies': [['Pinus taeda', 6888.0]]},
            {'nome': 'Serra da Esperança II', 'municipio': 'União da Vitória', 'uf': 'PR', 'area': 50.27, 'especies': [['Pinus taeda', 7205.0]]},
        ],
    },
    {
        'membro': 'REFLORESTADORA E AGROPECUARIA VALES DO HEBRON LTDA',
        'cnpj': '50.410.416/0001-56',
        'propriedades': [
            {'nome': 'Jarau', 'municipio': 'Marquinho', 'uf': 'PR', 'area': 20.93, 'especies': []},
        ],
    },
    {
        'membro': 'REFLORESTADORA NICHELE INDUSTRIA DE MADEIRAS LTDA',
        'cnpj': '89.076.277/0002-92',
        'propriedades': [
            {'nome': 'Sul I', 'municipio': 'Piratini', 'uf': 'RS', 'area': 1102.7, 'especies': [['Pinus elliottii', 454895.28]]},
            {'nome': 'Sul II', 'municipio': 'Piratini', 'uf': 'RS', 'area': 484.98, 'especies': [['Pinus elliottii', 140000.0], ['Eucalyptus sp', 31591.0]]},
        ],
    },
    {
        'membro': 'REFLORESTADORA SÃO MANOEL LTDA',
        'cnpj': '76.909.530/0001-19',
        'propriedades': [
            {'nome': 'Araras', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 107.73, 'especies': []},
            {'nome': 'Baú', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 594.78, 'especies': []},
            {'nome': 'Boa Vista', 'municipio': 'Inácio Martins', 'uf': 'PR', 'area': 390.13, 'especies': [['Pinus taeda', 774.69]]},
            {'nome': 'Cachoeira', 'municipio': 'Turvo', 'uf': 'PR', 'area': 32.39, 'especies': [['Pinus taeda', 4187.0]]},
            {'nome': 'Cantagalinho', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 37.14, 'especies': [['Pinus taeda', 12725.9]]},
            {'nome': 'Cantagalo', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 114.24, 'especies': [['Pinus taeda', 40075.3]]},
            {'nome': 'Carazinho', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 10.17, 'especies': [['Pinus taeda', 2052.036]]},
            {'nome': 'Cavaco', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 116.08, 'especies': [['Pinus taeda', 39524.0]]},
            {'nome': 'Fábrica de Pasta', 'municipio': 'Sta Maria do Oeste', 'uf': 'PR', 'area': 18.78, 'especies': [['Pinus taeda', 6934.69]]},
            {'nome': 'Faxinal das Araras', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 139.08, 'especies': []},
            {'nome': 'Faxinal dos Carpinteiros', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 92.9, 'especies': [['Pinus taeda', 24626.0]]},
            {'nome': 'Gabiroba', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 78.49, 'especies': [['Pinus taeda', 9614.0]]},
            {'nome': 'Jacutinga', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 71.7, 'especies': [['Pinus taeda', 18621.14]]},
            {'nome': 'Juquia de Cima', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 9.68, 'especies': [['Pinus taeda', 3661.4]]},
            {'nome': 'Marrecas e Santa Carlota', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 131.54, 'especies': [['Pinus taeda', 1941.632]]},
            {'nome': 'Monte Alvão', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 346.27, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'Palanque', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 17.62, 'especies': [['Pinus taeda', 4398.5097]]},
            {'nome': 'Parceria Jakob', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 183.48, 'especies': [['Pinus taeda', 5461.0]]},
            {'nome': 'Parceria Elias Farah', 'municipio': 'Reserva do Iguaçu', 'uf': 'PR', 'area': 466.03, 'especies': []},
            {'nome': 'Sabiá', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 239.78, 'especies': [['Pinus taeda', 71924.2]]},
            {'nome': 'Serro Verde', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 305.12, 'especies': []},
            {'nome': 'Parceria Ubirajara', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 18.16, 'especies': []},
            {'nome': 'Soncela II', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 126.96, 'especies': [['Pinus taeda', 13134.0]]},
            {'nome': 'Três Capões', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 162.8, 'especies': []},
            {'nome': 'Tunas e Tuninhas', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 230.11, 'especies': []},
            {'nome': 'Vividence', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 31.12, 'especies': []},
            {'nome': 'Xaxim Tigrinho', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 505.87, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'Parceria Helmuth', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 124.29, 'especies': []},
            {'nome': 'Parceria Neurete', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 48.59, 'especies': []},
            {'nome': 'Parceria Sônia Virmond', 'municipio': 'Candói', 'uf': 'PR', 'area': 425.76, 'especies': []},
            {'nome': 'Limoeiro', 'municipio': 'Candói', 'uf': 'PR', 'area': 75.21, 'especies': []},
        ],
    },
    {
        'membro': 'REFLORESTADORA SERPASTA LTDA',
        'cnpj': '97.339.691/0001-94',
        'propriedades': [
            {'nome': 'Bloco Cruz Machado', 'municipio': 'Cruz Machado', 'uf': 'PR', 'area': 622.72, 'especies': []},
            {'nome': 'Bloco Mallet', 'municipio': 'Mallet', 'uf': 'PR', 'area': 133.7, 'especies': []},
        ],
    },
    {
        'membro': 'RENATO BENAZZI LTDA',
        'cnpj': '906.759.247-15',
        'propriedades': [
            {'nome': 'Águas Claras', 'municipio': 'Doutor Ulysses', 'uf': 'PR', 'area': 69.96, 'especies': [['Pinus elliottii', 15109.2]]},
            {'nome': 'Benazzi', 'municipio': 'Piraí do Sul', 'uf': 'PR', 'area': 26.18, 'especies': [['Pinus elliottii', 6158.52]]},
            {'nome': 'Cercado Grande', 'municipio': 'Piraí do Sul', 'uf': 'PR', 'area': 45.37, 'especies': [['Pinus elliottii', 10860.12]]},
            {'nome': 'Chácara Bananal', 'municipio': 'Castro', 'uf': 'PR', 'area': 26.18, 'especies': [['Pinus elliottii', 8281.3188]]},
        ],
    },
    {
        'membro': 'RICARDO MARCELO BOBATO NETO',
        'cnpj': 'PENDENTE-034',
        'propriedades': [
            {'nome': 'Barreiros', 'municipio': 'Guamiranga', 'uf': 'PR', 'area': 89.54, 'especies': [['Pinus taeda', 19296.7]]},
        ],
    },
    {
        'membro': 'ROBERT REINHOFER',
        'cnpj': '036.893.259-19',
        'propriedades': [
            {'nome': 'Santa Isabel', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 2296.08, 'especies': [['Pinus taeda', 145129.02]]},
        ],
    },
    {
        'membro': 'RR TONIOLO REFLORESTAMENTO E EXTRAÇÃO DE MADEIRAS LTDA',
        'cnpj': '46.421.786/0001-11',
        'propriedades': [
            {'nome': 'Cerro Lindo', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 1429.96, 'especies': [['Pinus taeda', 169816.97], ['Eucalyptus dunnii', 169816.97], ['Pinus elliottii', 0.0]]},
            {'nome': 'Palmeirinha', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 378.65, 'especies': [['Pinus taeda', 50808.54], ['Eucalyptus dunnii', 50808.54]]},
        ],
    },
    {
        'membro': 'SALESIO PASSAÚRA',
        'cnpj': 'PENDENTE-035',
        'propriedades': [
            {'nome': 'Niasi', 'municipio': 'Jaguariaiva', 'uf': 'PR', 'area': 49.29, 'especies': [['Pinus taeda', 16604.5]]},
        ],
    },
    {
        'membro': 'SILVANA DIAS SILVEIRA',
        'cnpj': '29.116.865/0001-08',
        'propriedades': [
            {'nome': 'Bugio', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 286.1, 'especies': [['Pinus taeda', 28170.568], ['Eucalyptus dunnii', 8507.328]]},
            {'nome': 'Colonia 3 - II', 'municipio': 'Mallet', 'uf': 'PR', 'area': 35.08, 'especies': [['Pinus taeda', 7299.4]]},
            {'nome': 'Rio Corrente', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 301.49, 'especies': [['Pinus taeda', 52788.5738]]},
            {'nome': 'Riozinho', 'municipio': 'Rebouças', 'uf': 'PR', 'area': 124.0, 'especies': [['Pinus taeda', 14097.95]]},
            {'nome': 'Vera Cruz', 'municipio': 'Mallet', 'uf': 'PR', 'area': 19.2, 'especies': [['Pinus taeda', 0.0]]},
            {'nome': 'Vicinal 10', 'municipio': 'Mallet', 'uf': 'PR', 'area': 9.6, 'especies': [['Pinus taeda', 992.36]]},
            {'nome': 'Vicinal 6', 'municipio': 'Mallet', 'uf': 'PR', 'area': 25.8, 'especies': [['Pinus taeda', 3059.19]]},
        ],
    },
    {
        'membro': 'SILVESTRE GABRIEL PRZYBYSZ',
        'cnpj': '057.349.409-68',
        'propriedades': [
            {'nome': 'Araça', 'municipio': 'Mallet', 'uf': 'PR', 'area': 155.95, 'especies': [['Pinus taeda', 39704.605]]},
            {'nome': 'Lopuch', 'municipio': 'Mallet', 'uf': 'PR', 'area': 37.15, 'especies': [['Pinus taeda', 9141.155]]},
            {'nome': 'Pedreira', 'municipio': 'Mallet', 'uf': 'PR', 'area': 21.65, 'especies': [['Pinus taeda', 6635.44]]},
            {'nome': 'Santa Cruz do Rio Claro', 'municipio': 'Mallet', 'uf': 'PR', 'area': 47.42, 'especies': [['Pinus taeda', 22329.64]]},
            {'nome': 'Sítio Vidal', 'municipio': 'Mallet', 'uf': 'PR', 'area': 24.42, 'especies': [['Pinus taeda', 4671.933]]},
            {'nome': 'Tigre', 'municipio': 'Cruz Machado', 'uf': 'PR', 'area': 23.76, 'especies': [['Pinus taeda', 6356.64]]},
            {'nome': 'Traszkowski', 'municipio': 'Mallet', 'uf': 'PR', 'area': 45.4, 'especies': [['Pinus taeda', 4858.09]]},
        ],
    },
    {
        'membro': 'SOIL FLORESTAL LTDA',
        'cnpj': '51.679.608/0001-25',
        'propriedades': [
            {'nome': 'Cacumbangue', 'municipio': 'Coronel Domingos Soares', 'uf': 'PR', 'area': 137.5, 'especies': [['Pinus taeda', 26329.0], ['Eucalyptus grandis', 12191.0]]},
            {'nome': 'Santo Agostinho', 'municipio': 'Passos Maia', 'uf': 'SC', 'area': 844.23, 'especies': [['Pinus taeda', 63604.0]]},
        ],
    },
    {
        'membro': 'SUDATI AGROFLORESTAL LTDA',
        'cnpj': '44.577.869/0002-50',
        'propriedades': [
            {'nome': 'Araújo', 'municipio': 'Lages', 'uf': 'SC', 'area': 523.34, 'especies': [['Pinus taeda', 119282.45], ['Eucalyptus sp', 7284.684]]},
            {'nome': 'Santa Ana', 'municipio': 'Lages', 'uf': 'SC', 'area': 242.31, 'especies': [['Pinus taeda', 6683.412], ['Eucalyptus sp', 35027.83]]},
        ],
    },
    {
        'membro': 'THIAGO DIAS CESCHIM',
        'cnpj': '29.116.865/0001-08',
        'propriedades': [
            {'nome': 'Santa Cruz', 'municipio': 'Mallet', 'uf': 'PR', 'area': 520.66, 'especies': [['Pinus taeda', 75667.9127]]},
            {'nome': 'Santa Cruz do Rio Claro', 'municipio': 'Mallet', 'uf': 'PR', 'area': 233.69, 'especies': [['Pinus taeda', 22314.05]]},
            {'nome': 'Serro So I e II', 'municipio': 'Mallet', 'uf': 'PR', 'area': 423.3, 'especies': [['Pinus taeda', 2085.49]]},
            {'nome': 'Serro So III', 'municipio': 'Mallet', 'uf': 'PR', 'area': 219.66, 'especies': [['Pinus taeda', 1236.64]]},
            {'nome': 'Xarqueada', 'municipio': 'Mallet', 'uf': 'PR', 'area': 79.54, 'especies': [['Pinus taeda', 9101.04]]},
        ],
    },
    {
        'membro': 'TRANSMAB LTDA EPP',
        'cnpj': '16.958.843/0001-35',
        'propriedades': [
            {'nome': 'Vila Branca - Gleba A', 'municipio': 'Doutor Ulysses', 'uf': 'PR', 'area': 2212.46, 'especies': []},
            {'nome': 'Vila Branca - Gleba B', 'municipio': 'Doutor Ulysses', 'uf': 'PR', 'area': 102.85, 'especies': []},
        ],
    },
    {
        'membro': 'TRÊS CAPÕES S.A.',
        'cnpj': '76.909.530/0001-19',
        'propriedades': [
            {'nome': 'Araras', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 8.34, 'especies': []},
            {'nome': 'Capão Alto', 'municipio': 'Candói', 'uf': 'PR', 'area': 791.16, 'especies': []},
            {'nome': 'Goes Artigas', 'municipio': 'Inácio Martins', 'uf': 'PR', 'area': 303.37, 'especies': [['Pinus taeda', 58463.328]]},
            {'nome': 'Juquiá de Baixo', 'municipio': 'Cantagalo', 'uf': 'PR', 'area': 419.07, 'especies': [['Pinus taeda', 10302.551]]},
            {'nome': 'Limoeiro', 'municipio': 'Candói', 'uf': 'PR', 'area': 523.48, 'especies': []},
            {'nome': 'Palmeira', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 557.35, 'especies': []},
            {'nome': 'Serro Verde', 'municipio': 'Campina do Simão', 'uf': 'PR', 'area': 348.38, 'especies': []},
            {'nome': 'Três Capões', 'municipio': 'Guarapuava', 'uf': 'PR', 'area': 168.3, 'especies': []},
            {'nome': 'Tunas e Tuninhas', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 410.5, 'especies': []},
            {'nome': 'Vividence', 'municipio': 'Goioxin', 'uf': 'PR', 'area': 453.27, 'especies': []},
        ],
    },
    {
        'membro': 'TRIÂNGULO EMPREENDIMENTOS FLORESTAIS',
        'cnpj': '09.621.584/0001-97',
        'propriedades': [
            {'nome': 'Birituba', 'municipio': 'Tijucas do Sul', 'uf': 'PR', 'area': 234.15, 'especies': []},
            {'nome': 'Buriti', 'municipio': 'Campo do Tenente', 'uf': 'PR', 'area': 260.59, 'especies': []},
            {'nome': 'Campina', 'municipio': 'Tijucas do Sul', 'uf': 'PR', 'area': 704.34, 'especies': []},
            {'nome': 'Cascavel', 'municipio': 'Campo do Tenente', 'uf': 'PR', 'area': 224.26, 'especies': []},
            {'nome': 'Córrego Bonito', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 63.32, 'especies': []},
            {'nome': 'Figueira 1', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 337.64, 'especies': []},
            {'nome': 'Figueira 3', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 8.84, 'especies': []},
            {'nome': 'Figueira 6', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 42.66, 'especies': []},
            {'nome': 'Figueira IV', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 107.32, 'especies': []},
            {'nome': 'Figueira IX', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 48.1, 'especies': []},
            {'nome': 'Figueira V', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 68.27, 'especies': []},
            {'nome': 'Morro Grande', 'municipio': 'Rio Negro', 'uf': 'PR', 'area': 304.42, 'especies': []},
            {'nome': 'Retiro Bonito I', 'municipio': 'Rio Negro', 'uf': 'PR', 'area': 411.54, 'especies': []},
            {'nome': 'Retiro Bonito II', 'municipio': 'Rio Negro', 'uf': 'PR', 'area': 130.87, 'especies': []},
            {'nome': 'Ribeirão Grande 1', 'municipio': 'Agudos do Sul', 'uf': 'PR', 'area': 227.03, 'especies': []},
            {'nome': 'Ribeirão Grande 2', 'municipio': 'Agudos do Sul', 'uf': 'PR', 'area': 181.08, 'especies': []},
            {'nome': 'Ribeirão Grande III', 'municipio': 'Agudos do Sul', 'uf': 'PR', 'area': 277.23, 'especies': []},
            {'nome': 'Triângulo', 'municipio': 'Bocaiúva do Sul', 'uf': 'PR', 'area': 568.92, 'especies': []},
            {'nome': 'Figueira 2', 'municipio': 'Bocaiuva do Sul', 'uf': 'PR', 'area': 262.89, 'especies': []},
            {'nome': 'Figueira 10', 'municipio': 'Bocaiuva do Sul', 'uf': 'PR', 'area': 44.46, 'especies': []},
            {'nome': 'Ribeirão Grande 4', 'municipio': 'Agudos do Sul', 'uf': 'PR', 'area': 227.28, 'especies': []},
            {'nome': 'Sesmaria do Potunã', 'municipio': 'Bocaiuva do Sul', 'uf': 'PR', 'area': 55.21, 'especies': []},
        ],
    },
    {
        'membro': 'V W INDUSTRIA E COMERCIO DE MADEIRAS LTDA',
        'cnpj': '81.490.500/0001-50',
        'propriedades': [
            {'nome': 'Envolvido', 'municipio': 'Coronel Vivida', 'uf': 'PR', 'area': 85.32, 'especies': [['Eucalyptus sp', 17089.2], ['Pinus taeda', 4365.8]]},
            {'nome': 'Linha Borges', 'municipio': 'Coronel Vivida', 'uf': 'PR', 'area': 28.08, 'especies': [['Pinus taeda', 13631.72]]},
            {'nome': 'Passo da Erva', 'municipio': 'Chopinzinho', 'uf': 'PR', 'area': 76.74, 'especies': [['Eucalyptus sp', 1780.0], ['Pinus taeda', 20161.0]]},
            {'nome': 'Santa Lucia', 'municipio': 'Coronel Vivida', 'uf': 'PR', 'area': 13.21, 'especies': [['Araucaria angustifolia', 239.25], ['Pinus taeda', 4879.32]]},
            {'nome': 'Santa Terezinha', 'municipio': 'Coronel Vivida', 'uf': 'PR', 'area': 41.96, 'especies': [['Eucalyptus sp', 8760.82]]},
        ],
    },
]

def bootstrap_propriedades_fm(apps, schema_editor):
    Organization = apps.get_model('participants', 'Organization')
    Participant = apps.get_model('participants', 'Participant')
    Propriedade = apps.get_model('manejo', 'Propriedade')
    Especie = apps.get_model('manejo', 'Especie')
    InventarioEntrada = apps.get_model('manejo', 'InventarioEntrada')

    org = Organization.objects.first()
    if not org:
        org = Organization.objects.create(
            name='Solufor', slug='solufor',
            legal_name='Solufor Soluções Florestais', is_active=True,
        )

    hoje = date.today()
    stats = {'membros_novos': 0, 'membros_existentes': 0, 'propriedades': 0, 'especies': 0, 'entradas': 0}

    for item in MEMBROS_FM:
        cnpj = item['cnpj']
        membro = item['membro']

        participant, created = Participant.objects.get_or_create(
            cnpj=cnpj,
            defaults={
                'organization': org,
                'legal_name': membro,
                'trade_name': membro,
                'status': 'active',
                'ativo_coc': False,
                'ativo_fm': True,
            }
        )
        if created:
            stats['membros_novos'] += 1
        else:
            stats['membros_existentes'] += 1
            if not participant.ativo_fm:
                participant.ativo_fm = True
                participant.save()

        for prop_data in item['propriedades']:
            propriedade, _ = Propriedade.objects.get_or_create(
                participant=participant,
                nome=prop_data['nome'],
                defaults={
                    'municipio': prop_data['municipio'] or '',
                    'uf': prop_data['uf'] or '',
                    'area_hectares': prop_data['area'],
                    'ativa': True,
                }
            )
            stats['propriedades'] += 1

            for especie_nome, volume in prop_data['especies']:
                especie, esp_created = Especie.objects.get_or_create(
                    participant=participant,
                    nome=especie_nome,
                    defaults={
                        'fator_m3_para_ton': 1.04,
                        'fator_m3_para_st': 1.45,
                        'ativo': True,
                    }
                )
                if esp_created:
                    stats['especies'] += 1

                ja_existe = InventarioEntrada.objects.filter(
                    propriedade=propriedade, especie=especie
                ).exists()
                if not ja_existe:
                    InventarioEntrada.objects.create(
                        participant=participant,
                        propriedade=propriedade,
                        especie=especie,
                        data=hoje,
                        documento='Importação inicial',
                        volume=volume,
                        unidade='m3',
                        volume_m3=volume,
                        observacoes='Volume certificado importado da planilha de controle. Fatores de conversão m³→ton e m³→st são placeholders (1.04 / 1.45) e devem ser revisados por espécie/membro.',
                    )
                    stats['entradas'] += 1

    print(f"\n[Manejo FM] Membros novos: {stats['membros_novos']} | Membros já existentes (FM habilitado): {stats['membros_existentes']}")
    print(f"[Manejo FM] Propriedades: {stats['propriedades']} | Espécies: {stats['especies']} | Entradas de inventário: {stats['entradas']}")


class Migration(migrations.Migration):

    dependencies = [
        ('manejo', '0002_propriedade_municipio_propriedade_uf'),
        ('participants', '0007_participant_ativo_coc_participant_ativo_fm'),
    ]

    operations = [
        migrations.RunPython(bootstrap_propriedades_fm, migrations.RunPython.noop),
    ]
