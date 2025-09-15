"""
Teste simples do sistema de processamento paralelo de imagens.
Executa Sender e Worker em sequência para verificar funcionamento básico.
"""

import os
import sys
import time
import subprocess
from pgm_image import PGMImage


def create_test_image(filename: str) -> bool:
    """
    Cria uma imagem PGM de teste simples.
    """
    try:
        # Criar imagem 100x100 com padrão de teste
        image = PGMImage(100, 100, 255)
        
        # Criar padrão de teste (gradiente)
        data = bytearray()
        for y in range(100):
            for x in range(100):
                # Padrão de xadrez
                if (x + y) % 2 == 0:
                    value = 255
                else:
                    value = 0
                data.append(value)
        
        image.data = bytes(data)
        return image.save_to_file(filename)
        
    except Exception as e:
        print(f"Erro ao criar imagem de teste: {e}")
        return False


def load_existing_image(filename: str) -> bool:
    """
    Carrega uma imagem PGM existente e valida se é válida.
    
    Args:
        filename: Caminho para o arquivo PGM existente
        
    Returns:
        True se a imagem foi carregada e é válida, False caso contrário
    """
    try:
        if not os.path.exists(filename):
            print(f"Erro: Arquivo {filename} não encontrado")
            return False
        
        # Tentar carregar a imagem para validar
        image = PGMImage()
        if not image.load_from_file(filename):
            print(f"Erro: Arquivo {filename} não é uma imagem PGM válida")
            return False
        
        print(f"Imagem carregada com sucesso: {image.w}x{image.h} pixels")
        return True
        
    except Exception as e:
        print(f"Erro ao carregar imagem {filename}: {e}")
        return False


def create_example_image(filename: str) -> bool:
    """
    Cria uma imagem PGM de exemplo mais interessante para demonstração.
    
    Args:
        filename: Nome do arquivo para salvar a imagem
        
    Returns:
        True se criou com sucesso, False caso contrário
    """
    try:
        # Criar imagem 200x200 com padrão mais interessante
        image = PGMImage(200, 200, 255)
        
        data = bytearray()
        for y in range(200):
            for x in range(200):
                # Criar gradiente radial
                center_x, center_y = 100, 100
                distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                max_distance = 100  # Raio máximo
                
                # Normalizar distância e criar gradiente
                normalized_distance = min(distance / max_distance, 1.0)
                value = int(255 * (1 - normalized_distance))
                
                # Adicionar padrão de ondas
                wave = int(50 * (1 + 0.5 * (x / 20) + 0.3 * (y / 15)))
                value = (value + wave) % 256
                
                data.append(value)
        
        image.data = bytes(data)
        return image.save_to_file(filename)
        
    except Exception as e:
        print(f"Erro ao criar imagem de exemplo: {e}")
        return False


def test_negative_filter_direct(input_image: str = None):
    """
    Testa o filtro negativo processando diretamente (compatível com Windows).
    
    Args:
        input_image: Caminho para imagem PGM existente (opcional)
    """
    print("=== TESTE: FILTRO NEGATIVO (PROCESSAMENTO DIRETO) ===")
    
    # Usar imagem existente ou criar uma de teste
    if input_image:
        input_file = input_image
        if not load_existing_image(input_file):
            print("Erro: Falha ao carregar imagem existente")
            return False
    else:
        input_file = "test_input.pgm"
        if not create_test_image(input_file):
            print("Erro: Falha ao criar imagem de teste")
            return False
    
    output_file = "test_output_negative.pgm"
    
    try:
        # Carregar imagem
        print("1. Carregando imagem...")
        image = PGMImage()
        if not image.load_from_file(input_file):
            print("Erro: Falha ao carregar imagem")
            return False
        
        print(f"Imagem carregada: {image.w}x{image.h} pixels")
        
        # Processar com filtro negativo
        print("2. Aplicando filtro negativo...")
        from filters import apply_negative_filter
        
        # Processar toda a imagem
        processed_data = apply_negative_filter(image, 0, image.h)
        
        # Criar imagem processada
        processed_image = PGMImage(image.w, image.h, image.maxv)
        processed_image.data = processed_data
        
        # Salvar resultado
        print("3. Salvando resultado...")
        if processed_image.save_to_file(output_file):
            print(f"✓ Teste do filtro negativo: SUCESSO")
            print(f"  Imagem salva em: {output_file}")
            return True
        else:
            print("✗ Erro ao salvar imagem processada")
            return False
            
    except Exception as e:
        print(f"✗ Erro no teste: {e}")
        return False
    
    finally:
        # Limpar arquivos temporários (exceto a imagem de entrada se for fornecida pelo usuário)
        if not input_image and os.path.exists(input_file):
            try:
                os.remove(input_file)
            except:
                pass


def test_negative_filter(input_image: str = None):
    """
    Testa o filtro negativo usando o método apropriado para o sistema operacional.
    
    Args:
        input_image: Caminho para imagem PGM existente (opcional)
    """
    # No Windows, usar processamento direto devido a limitações com FIFOs
    if os.name == 'nt':
        return test_negative_filter_direct(input_image)
    
    # Em sistemas Unix/Linux, usar o método original com FIFOs
    print("=== TESTE: FILTRO NEGATIVO (COM FIFO) ===")
    
    # Usar imagem existente ou criar uma de teste
    if input_image:
        input_file = input_image
        if not load_existing_image(input_file):
            print("Erro: Falha ao carregar imagem existente")
            return False
    else:
        input_file = "test_input.pgm"
        if not create_test_image(input_file):
            print("Erro: Falha ao criar imagem de teste")
            return False
    
    fifo_path = "/tmp/test_pipe"
    output_file = "test_output_negative.pgm"
    
    try:
        # Limpar FIFO se existir
        if os.path.exists(fifo_path):
            os.remove(fifo_path)
        
        print("1. Iniciando Worker...")
        worker_cmd = [sys.executable, 'worker.py', fifo_path, output_file, '0', '4']
        worker_process = subprocess.Popen(worker_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguardar Worker abrir FIFO
        time.sleep(2)
        
        print("2. Iniciando Sender...")
        sender_cmd = [sys.executable, 'sender.py', fifo_path, input_file]
        sender_process = subprocess.Popen(sender_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Aguardar conclusão
        print("3. Aguardando conclusão...")
        sender_return = sender_process.wait()
        worker_return = worker_process.wait()
        
        # Verificar resultados
        if sender_return == 0 and worker_return == 0 and os.path.exists(output_file):
            print("  Teste do filtro negativo: SUCESSO")
            return True
        else:
            print(" Teste do filtro negativo: FALHOU")
            print(f"  Sender return code: {sender_return}")
            print(f"  Worker return code: {worker_return}")
            return False
            
    except Exception as e:
        print(f"✗ Erro no teste: {e}")
        return False
    
    finally:
        # Limpar arquivos
        for file in [input_file, output_file, fifo_path]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except:
                    pass


def main():
    """
    Executa os testes simples.
    
    Uso:
        python test_simple.py [imagem.pgm]
        python test_simple.py --create-example
        
    Se uma imagem PGM for fornecida, ela será usada ao invés de criar uma de teste.
    Use --create-example para criar uma imagem de exemplo interessante.
    """
    print("=== TESTES SIMPLES DO SISTEMA ===")
    
    # Verificar argumentos de linha de comando
    input_image = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--create-example":
            example_file = "example_image.pgm"
            print(f"Criando imagem de exemplo: {example_file}")
            if create_example_image(example_file):
                print(f"Imagem de exemplo criada: {example_file}")
                input_image = example_file
            else:
                print("Erro ao criar imagem de exemplo")
                sys.exit(1)
        else:
            input_image = sys.argv[1]
            print(f"Usando imagem existente: {input_image}")
    else:
        print("Nenhuma imagem especificada, criando imagem de teste...")
    
    # Verificar arquivos necessários
    required_files = ['sender.py', 'worker.py', 'pgm_image.py', 'filters.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Erro: Arquivo {file} não encontrado")
            sys.exit(1)
    
    # Executar testes
    test1_passed = test_negative_filter(input_image)
    
    # Resultado final
    print("\n=== RESULTADO DOS TESTES ===")
    print(f"Filtro Negativo: {' PASSOU' if test1_passed else ' FALHOU'}")
    
    if test1_passed:
        print("\n TESTE PASSOU!")
        return 0
    else:
        print("\nTESTE FALHOU!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
