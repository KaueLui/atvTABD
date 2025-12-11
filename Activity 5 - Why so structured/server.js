import express from "express";
import mongoose from "mongoose";
import morgan from "morgan";
import path from "path";
import { fileURLToPath } from "url";

import authorRoutes from "./routes/authors.js";
import bookRoutes from "./routes/books.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

app.use(express.json());


app.use(morgan("dev"));


app.use(express.static(path.join(__dirname, "public")));

// MongoDB
mongoose
  .connect(process.env.MONGO_URI || "mongodb://root:example@localhost:27017", { dbName: "library" })
  .then(() => console.log("MongoDB conectado"))
  .catch(err => console.error(err));

app.use("/authors", authorRoutes);
app.use("/books", bookRoutes);

app.listen(3000, () => {
  console.log("Servidor rodando: http://localhost:3000");
});
