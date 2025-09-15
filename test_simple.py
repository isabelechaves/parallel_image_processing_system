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


def test_negative_filter():
    """
    Testa o filtro negativo.
    """
    print("=== TESTE: FILTRO NEGATIVO ===")
    
    # Criar imagem de teste
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
            print("✓ Teste do filtro negativo: SUCESSO")
            return True
        else:
            print("✗ Teste do filtro negativo: FALHOU")
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
    """
    print("=== TESTES SIMPLES DO SISTEMA ===")
    
    # Verificar arquivos necessários
    required_files = ['sender.py', 'worker.py', 'pgm_image.py', 'filters.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Erro: Arquivo {file} não encontrado")
            sys.exit(1)
    
    # Executar testes
    test1_passed = test_negative_filter()
    
    # Resultado final
    print("\n=== RESULTADO DOS TESTES ===")
    print(f"Filtro Negativo: {'✓ PASSOU' if test1_passed else '✗ FALHOU'}")
    
    if test1_passed:
        print("\n🎉 TESTE PASSOU!")
        return 0
    else:
        print("\n❌ TESTE FALHOU!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
