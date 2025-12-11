import mongoose from "mongoose";

mongoose.connect("mongodb://root:example@localhost:27017", { dbName: "library" })
  .then(async () => {
    await mongoose.connection.db.dropDatabase();
    console.log("Banco apagado!");
    process.exit(0);
  })
  .catch(err => {
    console.error(err);
    process.exit(1);
  });
