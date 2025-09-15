# Sistema de Processamento Paralelo de Imagens

Este projeto implementa um sistema de processamento paralelo de imagens em Python, conforme as especificações do documento "Trabalho M1 - 2025-2.pdf". O sistema utiliza dois processos independentes que se comunicam via FIFO (Named Pipe) e threads para processamento paralelo.

## 🚀 Início Rápido

### 1. Executar Teste Simples
```bash
# Usar imagem de teste criada automaticamente
python test_simple.py

# Usar uma imagem PGM existente
python test_simple.py minha_imagem.pgm

# Criar uma imagem de exemplo interessante
python test_simple.py --create-example
```

### 2. Executar Demonstração Completa
```bash
python main.py
```

### 3. Uso Manual
```bash
# Terminal 1: Iniciar Worker
python worker.py /tmp/imgpipe output.pgm 0

# Terminal 2: Iniciar Sender
python sender.py /tmp/imgpipe input.pgm
```

## 🖼️ Usando Imagens Existentes

O sistema agora suporta o uso de imagens PGM existentes! Você pode:

1. **Usar sua própria imagem PGM:**
   ```bash
   python test_simple.py sua_imagem.pgm
   ```

2. **Criar uma imagem de exemplo interessante:**
   ```bash
   python test_simple.py --create-example
   ```

3. **Usar imagem de teste padrão (padrão de xadrez):**
   ```bash
   python test_simple.py
   ```

### Formatos Suportados
- **PGM P5**: Formato binário de imagens em tons de cinza
- **Dimensões**: Qualquer tamanho (o sistema se adapta automaticamente)
- **Valores**: 0-255 (8 bits por pixel)

## 📁 Estrutura do Projeto

```
parallel_image_processing_system/
├── pgm_image.py          # Classe para manipulação de imagens PGM
├── sender.py             # Processo Emissor (Sender)
├── worker.py             # Processo Trabalhador (Worker)
├── filters.py            # Filtros de imagem (negativo e limiarização)
├── main.py               # Script principal com demonstrações
├── test_simple.py        # Testes simples do sistema
├── example_usage.py      # Exemplos de uso programático
├── setup.py              # Script de configuração e instalação
├── requirements.txt      # Dependências do projeto
└── README.md             # Esta documentação
```

## 🔧 Requisitos

- Python 3.6 ou superior
- Sistema operacional com suporte a FIFOs (Linux, macOS, WSL no Windows)
- Apenas bibliotecas padrão do Python

## 📖 Documentação Completa

Para documentação detalhada, exemplos de uso e especificações técnicas, consulte os comentários nos arquivos do código.

## 🎯 Funcionalidades

- ✅ Processamento paralelo com threads
- ✅ Comunicação via FIFO entre processos
- ✅ Filtros de imagem (negativo e limiarização)
- ✅ Sincronização com mutex e semáforos
- ✅ Tratamento completo de erros
- ✅ Testes automatizados
- ✅ Exemplos de uso
