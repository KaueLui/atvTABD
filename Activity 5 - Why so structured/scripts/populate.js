import mongoose from "mongoose";
import { faker } from "@faker-js/faker";
import Author from "../models/Author.js";
import Book from "../models/Book.js";

// Conexão com MongoDB
mongoose
  .connect("mongodb://root:example@localhost:27017", { dbName: "library" })
  .then(() => console.log("MongoDB conectado"))
  .catch(err => console.error(err));

async function populate() {
  try {
    // Limpar collections existentes
    await Book.deleteMany();
    await Author.deleteMany();

    const authors = [];

    // Criar 10 autores falsos
    for (let i = 0; i < 50; i++) {
      const author = await Author.create({
        name: faker.person.fullName(),
        birthdate: faker.date.birthdate({ min: 1950, max: 2000, mode: "year" }),
        nationality: faker.location.country(),
        books: []
      });
      authors.push(author);
    }

    // Criar 50 livros aleatórios
    for (let i = 0; i < 100; i++) {
      // Seleciona um autor aleatório
      const author = authors[Math.floor(Math.random() * authors.length)];

      const book = await Book.create({
        title: faker.lorem.words({ min: 2, max: 5 }),
        author: author._id,
        publishedYear: faker.number.int({ min: 1950, max: 2025 }),
        genre: faker.music.genre(),
        isbn: faker.string.uuid()
      });

      // Adiciona referência do livro no autor
      author.books.push(book._id);
      await author.save();
    }

    console.log("Banco populado com sucesso!");
    process.exit(0);

  } catch (err) {
    console.error(err);
    process.exit(1);
  }
}

populate();
