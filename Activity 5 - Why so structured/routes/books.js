import express from "express";
import Book from "../models/Book.js";
import Author from "../models/Author.js";

const router = express.Router();

// Cadastra um livro
router.post("/", async (req, res) => {
  try {
    const book = await Book.create(req.body);
    await Author.findByIdAndUpdate(book.author, { $push: { books: book._id } });
    res.json(book);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Procura pelo id
router.get("/:id", async (req, res) => {
  try {
    const book = await Book.findById(req.params.id).populate("author");
    res.json(book);
  } catch {
    res.status(404).json({ error: "Livro não encontrado" });
  }
});

// Atualiza
router.put("/:id", async (req, res) => {
  try {
    const book = await Book.findByIdAndUpdate(req.params.id, req.body, { new: true });
    res.json(book);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Apaga um
router.delete("/:id", async (req, res) => {
  try {
    const book = await Book.findByIdAndDelete(req.params.id);
    if (book) {
      await Author.findByIdAndUpdate(book.author, { $pull: { books: book._id } });
    }
    res.json({ message: "Livro deletado" });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Mostra com páginação
router.get("/", async (req, res) => {
  const { page = 1, limit = 10, search = "" } = req.query;

  const query = search
    ? { title: { $regex: search, $options: "i" } }
    : {};

  const books = await Book.find(query)
    .skip((page - 1) * limit)
    .limit(Number(limit))
    .populate("author");

  res.json(books);
});

export default router;
