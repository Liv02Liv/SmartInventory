import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import json

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Inventores")
        self.root.geometry("900x700")
        self.root.configure(bg="#7196c0")

        # Variáveis de controle
        self.stock_data = {}
        self.item_locations = {}
        self.history = []
        self.location_counter = 1
        self.stock_limit_global = 100  # fallback se não houver max definido

        # Limites personalizados por item
        self.min_stock = {}
        self.max_stock = {}

        # Carregar dados persistentes
        self.load_data()

        # Configuração da interface
        self.create_widgets()

    def create_widgets(self):
        # Título
        title_label = tk.Label(self.root, text="Smart Inventores", font=("Arial", 18, "bold"), bg="#7196c0", fg="#ffffff")
        title_label.pack(pady=10)

        # Entrada de dados
        entry_frame = tk.Frame(self.root, bg="#7196c0")
        entry_frame.pack(pady=10)

        tk.Label(entry_frame, text="Item:", bg="#7196c0", fg="#ffffff").grid(row=0, column=0)
        self.item_entry = tk.Entry(entry_frame)
        self.item_entry.grid(row=0, column=1, padx=5)

        tk.Label(entry_frame, text="Quantidade:", bg="#7196c0", fg="#ffffff").grid(row=1, column=0)
        self.quantity_entry = tk.Entry(entry_frame)
        self.quantity_entry.grid(row=1, column=1, padx=5)

        # Botões principais
        button_style = {"width": 20, "padx": 5, "pady": 5}
        tk.Button(entry_frame, text="Registrar Entrada", command=self.register_entry, **button_style).grid(row=0, column=2)
        tk.Button(entry_frame, text="Registrar Saída", command=self.register_exit, **button_style).grid(row=1, column=2)
        tk.Button(entry_frame, text="Pesquisar Item", command=self.search_item, **button_style).grid(row=2, column=1, pady=5)
        tk.Button(entry_frame, text="Definir Limites", command=self.define_limits, **button_style).grid(row=2, column=2, pady=5)

        # Tabela de Estoque
        self.tree = ttk.Treeview(self.root, columns=("Item", "Quantidade", "Status", "Localização"), show="headings")
        self.tree.heading("Item", text="Item", anchor="center")
        self.tree.heading("Quantidade", text="Quantidade", anchor="center")
        self.tree.heading("Status", text="Status", anchor="center")
        self.tree.heading("Localização", text="Localização", anchor="center")

        self.tree.column("Item", anchor="center", width=200)
        self.tree.column("Quantidade", anchor="center", width=100)
        self.tree.column("Status", anchor="center", width=200)
        self.tree.column("Localização", anchor="center", width=200)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Barra de rolagem para a tabela
        tree_scroll = ttk.Scrollbar(self.root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Histórico
        tk.Label(self.root, text="Histórico de Entrada e Saída", bg="#7196c0", fg="#ffffff", font=("Arial", 12, "bold")).pack(pady=5)
        self.history_box = tk.Text(self.root, height=8, width=100)
        self.history_box.pack(pady=5)
        self.load_history_to_textbox()

        # Atualizar tabela ao carregar dados
        self.update_tree()

    def define_limits(self):
        """Abre uma janela para definir os limites mínimo e máximo do item selecionado."""
        item = self.item_entry.get().strip()
        if not item:
            messagebox.showerror("Erro", "Digite o nome do item para definir os limites.")
            return

        if item not in self.stock_data:
            messagebox.showerror("Erro", "Item não encontrado no estoque.")
            return

        # Valores atuais (ou padrões)
        current_min = self.min_stock.get(item, 0)
        current_max = self.max_stock.get(item, self.stock_limit_global)

        # Diálogo para entrada dos novos limites
        new_min = simpledialog.askinteger("Limite Mínimo", f"Digite o estoque mínimo para '{item}':", initialvalue=current_min)
        if new_min is None:
            return
        new_max = simpledialog.askinteger("Limite Máximo", f"Digite o estoque máximo para '{item}':", initialvalue=current_max)
        if new_max is None:
            return

        if new_min < 0 or new_max <= 0 or new_min >= new_max:
            messagebox.showerror("Erro", "Limites inválidos. Mínimo deve ser >=0 e máximo > mínimo.")
            return

        self.min_stock[item] = new_min
        self.max_stock[item] = new_max
        self.update_tree()
        self.save_data()
        messagebox.showinfo("Sucesso", f"Limites de '{item}' atualizados: mínimo={new_min}, máximo={new_max}")

    def register_entry(self):
        item = self.item_entry.get().strip()
        quantity = self.quantity_entry.get().strip()

        if not item or not quantity.isdigit():
            messagebox.showerror("Erro", "Insira dados válidos.")
            return

        quantity = int(quantity)

        # Atribuir localização ao item, se necessário
        if item not in self.item_locations:
            corridor = (self.location_counter - 1) // 25 + 1
            shelf = ((self.location_counter - 1) % 25) // 5 + 1
            level = (self.location_counter - 1) % 5 + 1
            self.item_locations[item] = f"C{corridor}E{shelf}P{level}"
            self.location_counter += 1

        # Atualizar estoque
        self.stock_data[item] = self.stock_data.get(item, 0) + quantity

        # Se não houver limites definidos para este item, definir padrões (opcional)
        if item not in self.min_stock:
            self.min_stock[item] = 0
            self.max_stock[item] = self.stock_limit_global

        # Adicionar ao histórico
        self.add_to_history(item, quantity, "Entrada")

        # Atualizar interface
        self.update_tree()
        self.check_stock_alert(item)
        self.save_data()

    def register_exit(self):
        item = self.item_entry.get().strip()
        quantity = self.quantity_entry.get().strip()

        if not item or not quantity.isdigit():
            messagebox.showerror("Erro", "Insira dados válidos.")
            return

        quantity = int(quantity)

        if item not in self.stock_data or self.stock_data[item] < quantity:
            messagebox.showerror("Erro", "Estoque insuficiente.")
            return

        # Verificar se o item está no estoque de segurança
        status, color = self.get_stock_status(item)
        if status == "Estoque de Segurança":
            confirm = messagebox.askyesno("Aviso", f"O item '{item}' está no estoque de segurança. Deseja continuar com a saída?")
            if not confirm:
                return

        # Atualizar estoque
        self.stock_data[item] -= quantity

        # Adicionar ao histórico
        self.add_to_history(item, quantity, "Saída")

        # Atualizar interface
        self.update_tree()
        self.check_stock_alert(item)
        self.save_data()

    def search_item(self):
        item = self.item_entry.get().strip()

        if item in self.stock_data:
            quantity = self.stock_data[item]
            location = self.item_locations.get(item, "Desconhecido")
            status, _ = self.get_stock_status(item)
            min_q = self.min_stock.get(item, 0)
            max_q = self.max_stock.get(item, self.stock_limit_global)
            messagebox.showinfo("Item Encontrado", 
                f"Item: {item}\nQuantidade: {quantity}\nLocalização: {location}\nStatus: {status}\nLimite Mínimo: {min_q}\nLimite Máximo: {max_q}")
        else:
            messagebox.showwarning("Não Encontrado", "Item não encontrado no estoque.")

    def add_to_history(self, item, quantity, action):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        record = f"{timestamp} - {action}: {quantity}x {item}\n"
        self.history.append(record)
        self.history_box.insert(tk.END, record)

    def load_history_to_textbox(self):
        for record in self.history:
            self.history_box.insert(tk.END, record)

    def update_tree(self):
        # Limpar tabela
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Preencher tabela com dados atualizados
        for item, quantity in self.stock_data.items():
            location = self.item_locations.get(item, "Desconhecido")
            status, color = self.get_stock_status(item)
            self.tree.insert("", tk.END, values=(item, quantity, status, location), tags=(color,))

        # Configurar cores das linhas
        self.tree.tag_configure("verde", background="#00FF00")
        self.tree.tag_configure("amarelo", background="#FFFD00")
        self.tree.tag_configure("vermelho", background="#F20505")
        self.tree.tag_configure("cinza", background="#E2DEDE")

    def check_stock_alert(self, item):
        """Alerta baseado nos limites personalizados do item."""
        if item not in self.stock_data:
            return

        qty = self.stock_data[item]
        min_q = self.min_stock.get(item, 0)
        max_q = self.max_stock.get(item, self.stock_limit_global)

        # Percentual em relação ao máximo (para alerta de ponto de pedido)
        percentage = (qty / max_q) * 100 if max_q > 0 else 0

        if min_q > 0 and qty <= min_q:
            messagebox.showerror("Estoque Crítico", f"O item '{item}' está no estoque de segurança (abaixo de {min_q})!")
        elif 40 <= percentage <= 50:
            messagebox.showwarning("Alerta de Estoque", f"O item '{item}' está no ponto de fazer pedido (40-50% do máximo).")

    def get_stock_status(self, item):
        """Retorna status e cor com base nos limites do item (ou fallback global)."""
        qty = self.stock_data[item]
        min_q = self.min_stock.get(item, 0)
        max_q = self.max_stock.get(item, self.stock_limit_global)

        if qty == 0:
            return "Indisponível", "cinza"
        elif qty > max_q * 0.5:          # acima de 50% do máximo
            return "Disponível", "verde"
        elif qty > min_q:                # entre mínimo e 50% do máximo
            return "Fazer Pedido", "amarelo"
        else:                            # qty <= min_q
            return "Estoque de Segurança", "vermelho"

    def save_data(self):
        data = {
            "stock_data": self.stock_data,
            "item_locations": self.item_locations,
            "history": self.history,
            "location_counter": self.location_counter,
            "min_stock": self.min_stock,
            "max_stock": self.max_stock,
        }
        with open("inventory_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def load_data(self):
        try:
            with open("inventory_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.stock_data = data.get("stock_data", {})
                self.item_locations = data.get("item_locations", {})
                self.history = data.get("history", [])
                self.location_counter = data.get("location_counter", 1)
                self.min_stock = data.get("min_stock", {})
                self.max_stock = data.get("max_stock", {})

                # Garantir que todo item em stock_data tenha uma localização
                for item in self.stock_data:
                    if item not in self.item_locations:
                        corridor = (self.location_counter - 1) // 25 + 1
                        shelf = ((self.location_counter - 1) % 25) // 5 + 1
                        level = (self.location_counter - 1) % 5 + 1
                        self.item_locations[item] = f"C{corridor}E{shelf}P{level}"
                        self.location_counter += 1

                # Se algum item não tiver limites definidos, definir padrões (opcional)
                for item in self.stock_data:
                    if item not in self.min_stock:
                        self.min_stock[item] = 0
                        self.max_stock[item] = self.stock_limit_global

        except FileNotFoundError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()