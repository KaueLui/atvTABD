import express from "express";
import Author from "../models/Author.js";
import Book from "../models/Book.js";

const router = express.Router();

// Vai criar um autor
router.post("/", async (req, res) => {
  try {
    const author = await Author.create(req.body);
    res.json(author);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Procura o autor
router.get("/:id", async (req, res) => {
  try {
    const author = await Author.findById(req.params.id).populate("books");
    res.json(author);
  } catch {
    res.status(404).json({ error: "Autor não encontrado" });
  }
});

// Atualiza
router.put("/:id", async (req, res) => {
  try {
    const author = await Author.findByIdAndUpdate(req.params.id, req.body, { new: true });
    res.json(author);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Apaga o autor e seus livros
router.delete("/:id", async (req, res) => {
  try {
    const authorId = req.params.id;
    await Book.deleteMany({ author: authorId });
    await Author.findByIdAndDelete(authorId);
    res.json({ message: "Autor e livros deletados" });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Mostra os autores com paginação e busca
router.get("/", async (req, res) => {
  const { page = 1, limit = 10, search = "" } = req.query;

  const query = search
    ? { name: { $regex: search, $options: "i" } }
    : {};

  const authors = await Author.find(query)
    .skip((page - 1) * limit)
    .limit(Number(limit));

  res.json(authors);
});

export default router;
