"""
Módulo para manipulação de imagens PGM (P5).
Implementa leitura, escrita e processamento de imagens no formato PGM P5.
"""

import struct
import os
from typing import Tuple, Optional


class PGMImage:
    """
    Classe para representar e manipular imagens PGM (P5).
    
    Atributos:
        w (int): Largura da imagem
        h (int): Altura da imagem
        maxv (int): Valor máximo de intensidade (geralmente 255)
        data (bytes): Dados dos pixels da imagem
    """
    
    def __init__(self, width: int = 0, height: int = 0, max_value: int = 255):
        """
        Inicializa uma imagem PGM vazia.
        
        Args:
            width: Largura da imagem
            height: Altura da imagem
            max_value: Valor máximo de intensidade
        """
        self.w = width
        self.h = height
        self.maxv = max_value
        self.data = b''
    
    def load_from_file(self, filepath: str) -> bool:
        """
        Carrega uma imagem PGM do arquivo.
        
        Args:
            filepath: Caminho para o arquivo PGM
            
        Returns:
            True se carregou com sucesso, False caso contrário
        """
        try:
            with open(filepath, 'rb') as f:
                # Verificar cabeçalho P5
                magic = f.read(2)
                if magic != b'P5':
                    print(f"Erro: Arquivo {filepath} não é um PGM P5 válido")
                    return False
                
                # Pular comentários e espaços em branco
                f.readline()  # Pular primeira linha após P5
                
                # Ler dimensões
                line = f.readline().decode('ascii').strip()
                while line.startswith('#'):
                    line = f.readline().decode('ascii').strip()
                
                dimensions = line.split()
                if len(dimensions) != 2:
                    print(f"Erro: Formato de dimensões inválido em {filepath}")
                    return False
                
                self.w = int(dimensions[0])
                self.h = int(dimensions[1])
                
                # Ler valor máximo
                line = f.readline().decode('ascii').strip()
                while line.startswith('#'):
                    line = f.readline().decode('ascii').strip()
                
                self.maxv = int(line)
                
                # Ler dados dos pixels
                self.data = f.read()
                
                # Verificar se o tamanho dos dados está correto
                expected_size = self.w * self.h
                if len(self.data) != expected_size:
                    print(f"Erro: Tamanho dos dados incorreto. Esperado: {expected_size}, Encontrado: {len(self.data)}")
                    return False
                
                return True
                
        except FileNotFoundError:
            print(f"Erro: Arquivo {filepath} não encontrado")
            return False
        except Exception as e:
            print(f"Erro ao carregar {filepath}: {e}")
            return False
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Salva a imagem PGM em arquivo.
        
        Args:
            filepath: Caminho para salvar o arquivo
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            with open(filepath, 'wb') as f:
                # Escrever cabeçalho PGM P5
                f.write(b'P5\n')
                f.write(f'{self.w} {self.h}\n'.encode('ascii'))
                f.write(f'{self.maxv}\n'.encode('ascii'))
                
                # Escrever dados dos pixels
                f.write(self.data)
                
            return True
            
        except Exception as e:
            print(f"Erro ao salvar {filepath}: {e}")
            return False
    
    def get_pixel(self, x: int, y: int) -> int:
        """
        Obtém o valor de um pixel na posição (x, y).
        
        Args:
            x: Coordenada x (coluna)
            y: Coordenada y (linha)
            
        Returns:
            Valor do pixel (0-255)
        """
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return 0
        
        index = y * self.w + x
        return self.data[index]
    
    def set_pixel(self, x: int, y: int, value: int) -> None:
        """
        Define o valor de um pixel na posição (x, y).
        
        Args:
            x: Coordenada x (coluna)
            y: Coordenada y (linha)
            value: Valor do pixel (0-255)
        """
        if x < 0 or x >= self.w or y < 0 or y >= self.h:
            return
        
        index = y * self.w + x
        # Converter bytes para bytearray para permitir modificação
        if isinstance(self.data, bytes):
            self.data = bytearray(self.data)
        
        self.data[index] = max(0, min(255, value))
    
    def get_pixel_row(self, row: int) -> bytes:
        """
        Obtém uma linha completa da imagem.
        
        Args:
            row: Número da linha (0-based)
            
        Returns:
            Bytes da linha
        """
        if row < 0 or row >= self.h:
            return b''
        
        start = row * self.w
        end = start + self.w
        return self.data[start:end]
    
    def set_pixel_row(self, row: int, data: bytes) -> None:
        """
        Define uma linha completa da imagem.
        
        Args:
            row: Número da linha (0-based)
            data: Dados da linha
        """
        if row < 0 or row >= self.h or len(data) != self.w:
            return
        
        start = row * self.w
        end = start + self.w
        
        # Converter bytes para bytearray se necessário
        if isinstance(self.data, bytes):
            self.data = bytearray(self.data)
        
        self.data[start:end] = data
    
    def get_size(self) -> Tuple[int, int]:
        """
        Retorna as dimensões da imagem.
        
        Returns:
            Tupla (largura, altura)
        """
        return (self.w, self.h)
    
    def get_data_size(self) -> int:
        """
        Retorna o tamanho dos dados de pixels.
        
        Returns:
            Número de bytes dos dados
        """
        return len(self.data)
