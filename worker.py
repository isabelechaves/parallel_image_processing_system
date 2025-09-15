"""
Processo Trabalhador (Worker) para o sistema de processamento paralelo de imagens.
Responsável por receber dados via FIFO e processar com threads paralelas.
"""

import os
import sys
import struct
import threading
import time
from typing import List, Optional
from queue import Queue, Empty
from pgm_image import PGMImage
from sender import ImageHeader
from filters import process_image_rows


class Task:
    """
    Estrutura para representar uma tarefa de processamento.
    """
    
    def __init__(self, row_start: int, row_end: int):
        self.row_start = row_start
        self.row_end = row_end
    
    def __str__(self):
        return f"Task(rows {self.row_start}-{self.row_end-1})"


class WorkerThread(threading.Thread):
    """
    Thread trabalhador para processamento paralelo de imagens.
    """
    
    def __init__(self, thread_id: int, task_queue: Queue, result_data: dict,
                 image: PGMImage, mode: int, t1: int, t2: int,
                 mutex: threading.Lock, semaphore: threading.Semaphore,
                 completion_semaphore: threading.Semaphore):
        super().__init__()
        self.thread_id = thread_id
        self.task_queue = task_queue
        self.result_data = result_data
        self.image = image
        self.mode = mode
        self.t1 = t1
        self.t2 = t2
        self.mutex = threading.Lock()
        self.semaphore = semaphore
        self.completion_semaphore = completion_semaphore
        self.running = True
    
    def run(self):
        """
        Executa o loop principal da thread trabalhador.
        """
        print(f"Thread {self.thread_id} iniciada")
        
        while self.running:
            try:
                # Aguardar semáforo para obter tarefa
                self.semaphore.acquire()
                
                # Obter tarefa da fila (com timeout para permitir shutdown)
                try:
                    task = self.task_queue.get(timeout=0.1)
                except Empty:
                    self.semaphore.release()
                    continue
                
                print(f"Thread {self.thread_id} processando {task}")
                
                # Processar a tarefa
                processed_data = process_image_rows(
                    self.image, task.row_start, task.row_end, 
                    self.mode, self.t1, self.t2
                )
                
                # Armazenar resultado de forma thread-safe
                with self.mutex:
                    # Armazenar dados processados por linha
                    for i, row in enumerate(range(task.row_start, task.row_end)):
                        row_data = processed_data[i * self.image.w:(i + 1) * self.image.w]
                        self.result_data[row] = row_data
                
                print(f"Thread {self.thread_id} concluiu {task}")
                
                # Marcar tarefa como concluída
                self.task_queue.task_done()
                
                # Sinalizar conclusão
                self.completion_semaphore.release()
                
            except Exception as e:
                print(f"Erro na thread {self.thread_id}: {e}")
                self.semaphore.release()
        
        print(f"Thread {self.thread_id} finalizada")


class ParallelImageProcessor:
    """
    Processador de imagens com paralelização por threads.
    """
    
    def __init__(self, nthreads: int = 4):
        self.nthreads = nthreads
        self.threads: List[WorkerThread] = []
        self.task_queue = Queue()
        self.result_data = {}
        self.mutex = threading.Lock()
        self.semaphore = threading.Semaphore(0)  # Contador de tarefas disponíveis
        self.completion_semaphore = threading.Semaphore(0)  # Contador de tarefas concluídas
    
    def create_tasks(self, image_height: int, rows_per_task: int = 10) -> None:
        """
        Cria tarefas de processamento dividindo a imagem em subconjuntos de linhas.
        
        Args:
            image_height: Altura da imagem
            rows_per_task: Número de linhas por tarefa
        """
        print(f"Criando tarefas: {rows_per_task} linhas por tarefa")
        
        row_start = 0
        task_count = 0
        
        while row_start < image_height:
            row_end = min(row_start + rows_per_task, image_height)
            task = Task(row_start, row_end)
            self.task_queue.put(task)
            task_count += 1
            row_start = row_end
        
        print(f"Criadas {task_count} tarefas")
        
        # Liberar semáforos para as tarefas
        for _ in range(task_count):
            self.semaphore.release()
    
    def start_threads(self, image: PGMImage, mode: int, t1: int = 0, t2: int = 0) -> None:
        """
        Inicia as threads trabalhadoras.
        
        Args:
            image: Imagem a ser processada
            mode: Modo de processamento
            t1: Limite inferior para slice
            t2: Limite superior para slice
        """
        print(f"Iniciando {self.nthreads} threads trabalhadoras...")
        
        self.threads = []
        for i in range(self.nthreads):
            thread = WorkerThread(
                i, self.task_queue, self.result_data, image, mode, t1, t2,
                self.mutex, self.semaphore, self.completion_semaphore
            )
            thread.start()
            self.threads.append(thread)
    
    def wait_for_completion(self, total_tasks: int) -> None:
        """
        Aguarda a conclusão de todas as tarefas.
        
        Args:
            total_tasks: Número total de tarefas
        """
        print(f"Aguardando conclusão de {total_tasks} tarefas...")
        
        # Aguardar todas as tarefas serem concluídas
        for _ in range(total_tasks):
            self.completion_semaphore.acquire()
        
        print("Todas as tarefas foram concluídas!")
    
    def stop_threads(self) -> None:
        """
        Para todas as threads trabalhadoras.
        """
        print("Parando threads trabalhadoras...")
        
        for thread in self.threads:
            thread.running = False
        
        # Liberar semáforos para permitir que as threads saiam do loop
        for _ in range(self.nthreads):
            self.semaphore.release()
        
        # Aguardar threads terminarem
        for thread in self.threads:
            thread.join()
        
        print("Todas as threads foram paradas")
    
    def assemble_result(self, image: PGMImage) -> PGMImage:
        """
        Monta a imagem final a partir dos resultados das threads.
        
        Args:
            image: Imagem original de referência
            
        Returns:
            Imagem processada
        """
        print("Montando imagem final...")
        
        # Criar nova imagem com as mesmas dimensões
        result_image = PGMImage(image.w, image.h, image.maxv)
        result_image.data = bytearray(image.w * image.h)
        
        # Copiar dados processados linha por linha
        for row in range(image.h):
            if row in self.result_data:
                row_data = self.result_data[row]
                result_image.set_pixel_row(row, row_data)
            else:
                print(f"Aviso: Linha {row} não foi processada")
        
        return result_image


def receive_image_data(fifo_path: str) -> tuple[PGMImage, int, int, int]:
    """
    Recebe dados da imagem via FIFO.
    
    Args:
        fifo_path: Caminho para o FIFO
        
    Returns:
        Tupla (imagem, mode, t1, t2)
    """
    try:
        print(f"Abrindo FIFO {fifo_path} para leitura...")
        
        with open(fifo_path, 'rb') as fifo:
            print("FIFO aberto para leitura, recebendo dados...")
            
            # Receber cabeçalho
            header_data = fifo.read(24)  # 6 * 4 bytes
            if len(header_data) != 24:
                raise ValueError(f"Tamanho de cabeçalho inválido: {len(header_data)} bytes")
            
            header = ImageHeader.unpack(header_data)
            print(f"Cabeçalho recebido: {header.w}x{header.h}, max={header.maxv}, mode={header.mode}")
            
            # Criar imagem
            image = PGMImage(header.w, header.h, header.maxv)
            
            # Receber dados dos pixels
            expected_size = header.w * header.h
            image.data = fifo.read(expected_size)
            
            if len(image.data) != expected_size:
                raise ValueError(f"Tamanho de dados incorreto. Esperado: {expected_size}, Recebido: {len(image.data)}")
            
            print(f"Dados recebidos: {len(image.data)} bytes")
            return image, header.mode, header.t1, header.t2
            
    except Exception as e:
        print(f"Erro ao receber dados via FIFO: {e}")
        raise


def main_worker(fifo_path: str, output_image_path: str, mode: int, 
                t1: int = None, t2: int = None, nthreads: int = 4) -> None:
    """
    Função principal do Processo Trabalhador.
    
    Args:
        fifo_path: Caminho para o FIFO de comunicação
        output_image_path: Caminho para salvar a imagem processada
        mode: Modo de processamento (0=negativo, 1=slice)
        t1: Limite inferior para slice (opcional)
        t2: Limite superior para slice (opcional)
        nthreads: Número de threads para processamento
    """
    print("=== PROCESSO TRABALHADOR (WORKER) ===")
    print(f"FIFO: {fifo_path}")
    print(f"Imagem de saída: {output_image_path}")
    print(f"Modo: {'Negativo' if mode == 0 else 'Limiarização'}")
    print(f"Threads: {nthreads}")
    
    if mode == 1:
        if t1 is None or t2 is None:
            print("Erro: Modo slice requer parâmetros t1 e t2")
            sys.exit(1)
        print(f"Limites: t1={t1}, t2={t2}")
    
    try:
        # Receber dados via FIFO
        image, received_mode, received_t1, received_t2 = receive_image_data(fifo_path)
        
        # Usar parâmetros recebidos se não foram fornecidos
        if mode == -1:  # Modo não especificado, usar o recebido
            mode = received_mode
            t1 = received_t1
            t2 = received_t2
        
        print(f"Imagem recebida: {image.w}x{image.h}, max_value={image.maxv}")
        
        # Criar processador paralelo
        processor = ParallelImageProcessor(nthreads)
        
        # Criar tarefas
        rows_per_task = max(1, image.h // (nthreads * 4))  # Dividir em ~4 tarefas por thread
        processor.create_tasks(image.h, rows_per_task)
        
        # Iniciar threads
        start_time = time.time()
        processor.start_threads(image, mode, t1, t2)
        
        # Aguardar conclusão
        total_tasks = processor.task_queue.qsize()
        processor.wait_for_completion(total_tasks)
        
        # Montar resultado
        result_image = processor.assemble_result(image)
        
        # Parar threads
        processor.stop_threads()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"Processamento concluído em {processing_time:.2f} segundos")
        
        # Salvar imagem processada
        if result_image.save_to_file(output_image_path):
            print(f"Imagem salva: {output_image_path}")
        else:
            print("Erro: Falha ao salvar imagem")
            sys.exit(1)
        
        print("Processo Trabalhador concluído com sucesso!")
        
    except Exception as e:
        print(f"Erro no Processo Trabalhador: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python worker.py <fifo_path> <output_image_path> <mode> [t1] [t2] [nthreads]")
        print("  mode: 0=negativo, 1=slice, -1=usar modo recebido")
        print("  t1, t2: limites para modo slice (opcional)")
        print("  nthreads: número de threads (padrão: 4)")
        print("Exemplo: python worker.py /tmp/imgpipe output.pgm 0")
        print("Exemplo: python worker.py /tmp/imgpipe output.pgm 1 50 200 8")
        sys.exit(1)
    
    fifo_path = sys.argv[1]
    output_image_path = sys.argv[2]
    mode = int(sys.argv[3])
    
    t1 = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != 'None' else None
    t2 = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != 'None' else None
    nthreads = int(sys.argv[6]) if len(sys.argv) > 6 else 4
    
    main_worker(fifo_path, output_image_path, mode, t1, t2, nthreads)
