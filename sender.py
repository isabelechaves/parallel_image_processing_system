"""
Processo Emissor (Sender) para o sistema de processamento paralelo de imagens.
Responsável por carregar imagens PGM e transmitir via FIFO para o Processo Trabalhador.
"""

import os
import sys
import struct
import time
from typing import Optional
from pgm_image import PGMImage


class ImageHeader:
    """
    Estrutura para metadados da imagem a serem transmitidos via FIFO.
    """
    
    def __init__(self, width: int = 0, height: int = 0, max_value: int = 255, 
                 mode: int = 0, t1: int = 0, t2: int = 0):
        self.w = width
        self.h = height
        self.maxv = max_value
        self.mode = mode  # 0 para negativo, 1 para slice
        self.t1 = t1      # Limite inferior para slice
        self.t2 = t2      # Limite superior para slice
    
    def pack(self) -> bytes:
        """
        Empacota os metadados em bytes para transmissão.
        
        Returns:
            Bytes empacotados dos metadados
        """
        # Formato: 6 inteiros de 32 bits (little-endian)
        return struct.pack('<6I', self.w, self.h, self.maxv, self.mode, self.t1, self.t2)
    
    @classmethod
    def unpack(cls, data: bytes) -> 'ImageHeader':
        """
        Desempacota bytes em metadados.
        
        Args:
            data: Bytes dos metadados
            
        Returns:
            Instância de ImageHeader
        """
        if len(data) != 24:  # 6 * 4 bytes
            raise ValueError(f"Tamanho de dados inválido: {len(data)} bytes")
        
        w, h, maxv, mode, t1, t2 = struct.unpack('<6I', data)
        return cls(w, h, maxv, mode, t1, t2)


def create_fifo(fifo_path: str) -> bool:
    """
    Cria um FIFO nomeado se ele não existir.
    
    Args:
        fifo_path: Caminho para o FIFO
        
    Returns:
        True se criou com sucesso, False caso contrário
    """
    try:
        # Verificar se o FIFO já existe
        if os.path.exists(fifo_path):
            # Se existe, verificar se é um FIFO
            if not os.path.isdir(fifo_path):
                print(f"FIFO {fifo_path} já existe")
                return True
            else:
                print(f"Erro: {fifo_path} é um diretório, não um FIFO")
                return False
        
        # Criar o FIFO
        os.mkfifo(fifo_path)
        print(f"FIFO {fifo_path} criado com sucesso")
        return True
        
    except OSError as e:
        print(f"Erro ao criar FIFO {fifo_path}: {e}")
        return False


def send_image_data(fifo_path: str, image: PGMImage, mode: int, t1: int = 0, t2: int = 0) -> bool:
    """
    Envia dados da imagem via FIFO.
    
    Args:
        fifo_path: Caminho para o FIFO
        image: Imagem PGM a ser enviada
        mode: Modo de processamento (0=negativo, 1=slice)
        t1: Limite inferior para slice
        t2: Limite superior para slice
        
    Returns:
        True se enviou com sucesso, False caso contrário
    """
    try:
        print(f"Abrindo FIFO {fifo_path} para escrita...")
        
        # Abrir FIFO para escrita (bloqueia até que alguém abra para leitura)
        with open(fifo_path, 'wb') as fifo:
            print("FIFO aberto para escrita, enviando dados...")
            
            # Criar e enviar cabeçalho
            header = ImageHeader(image.w, image.h, image.maxv, mode, t1, t2)
            header_data = header.pack()
            
            print(f"Enviando cabeçalho: {image.w}x{image.h}, max={image.maxv}, mode={mode}")
            fifo.write(header_data)
            fifo.flush()
            
            # Enviar dados dos pixels
            print(f"Enviando {len(image.data)} bytes de dados de pixels...")
            fifo.write(image.data)
            fifo.flush()
            
            print("Dados enviados com sucesso!")
            return True
            
    except Exception as e:
        print(f"Erro ao enviar dados via FIFO: {e}")
        return False


def main_sender(fifo_path: str, input_image_path: str) -> None:
    """
    Função principal do Processo Emissor.
    
    Args:
        fifo_path: Caminho para o FIFO de comunicação
        input_image_path: Caminho para a imagem de entrada
    """
    print("=== PROCESSO EMISSOR (SENDER) ===")
    print(f"FIFO: {fifo_path}")
    print(f"Imagem de entrada: {input_image_path}")
    
    # Verificar se a imagem de entrada existe
    if not os.path.exists(input_image_path):
        print(f"Erro: Arquivo {input_image_path} não encontrado")
        sys.exit(1)
    
    # Carregar imagem PGM
    print("Carregando imagem PGM...")
    image = PGMImage()
    if not image.load_from_file(input_image_path):
        print("Erro: Falha ao carregar imagem")
        sys.exit(1)
    
    print(f"Imagem carregada: {image.w}x{image.h}, max_value={image.maxv}")
    
    # Criar FIFO se necessário
    if not create_fifo(fifo_path):
        print("Erro: Falha ao criar FIFO")
        sys.exit(1)
    
    # Para este exemplo, vamos usar modo negativo (0)
    # Em um sistema real, estes parâmetros viriam da linha de comando
    mode = 0  # Negativo
    t1 = 0
    t2 = 0
    
    print(f"Modo de processamento: {'Negativo' if mode == 0 else 'Limiarização'}")
    if mode == 1:
        print(f"Limites: t1={t1}, t2={t2}")
    
    # Enviar dados via FIFO
    if send_image_data(fifo_path, image, mode, t1, t2):
        print("Processo Emissor concluído com sucesso!")
    else:
        print("Erro: Falha no envio de dados")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python sender.py <fifo_path> <input_image_path>")
        print("Exemplo: python sender.py /tmp/imgpipe input.pgm")
        sys.exit(1)
    
    fifo_path = sys.argv[1]
    input_image_path = sys.argv[2]
    
    main_sender(fifo_path, input_image_path)
