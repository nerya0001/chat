class Window:
    def __init__(self, max_size, head, tail, size):
        self.queue = [None] * max_size
        self.head = head
        self.tail = tail
        self.size = size
        self.maxSize = max_size

    # Adding elements to the queue
    def enqueue(self, data):
        if self.is_full():
            return 'Queue full'
        self.queue[self.tail] = data
        self.tail = (self.tail + 1) % self.maxSize
        self.size += 1
        return True

    # Removing elements from the queue
    def dequeue(self):
        if self.is_empty():
            return 'Queue empty'
        # data = self.remove(seq)
        # print(f'self: {self.queue}')
        data = self.queue[self.head]

        # print(f'head: {self.head}')
        # print(f'data: {data}')
        self.queue[self.head] = None
        self.head = (self.head + 1) % self.maxSize
        self.size -= 1
        return data

    # Getter
    def get_index(self, index):
        if index > self.size:
            return 'Invalid index'
        # print(f'head: {self.head}')
        real_index = (index + self.head) % self.maxSize
        return self.queue[real_index]

    # Setter
    def set_index(self, index, value):
        if index > self.size:
            return 'Invalid index'
        real_index = (index + self.head) % self.maxSize
        self.queue[real_index] = value
        return True

    # Get size
    def num_elem(self):
        return self.size

    # Check if full
    def is_full(self):
        return self.size == self.maxSize

    # Check if empty
    def is_empty(self):
        return self.size == 0

    def __repr__(self):
        return str(self.queue)
