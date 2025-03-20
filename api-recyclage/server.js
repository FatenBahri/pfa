const express = require("express");
const fs = require("fs");
const csv = require("csv-parser");
const cors = require("cors");

const app = express();
const QRCode = require("qrcode");

const PORT = 3000;

app.use(cors()); // Autoriser les requêtes depuis Flutter

// Route pour lire les données du fichier CSV
app.get("/data", (req, res) => {
  let results = [];

  fs.createReadStream("bottle_trash_counts.csv")
    .pipe(csv())
    .on("data", (data) => results.push(data))
    .on("end", () => {
      res.json(results);
    });
});
// Génération du QR Code pour un utilisateur
app.get("/generate-qr/:userId", async (req, res) => {
    const userId = req.params.userId;
    const qrData = `USER-${userId}`;

    try {
        // Générer le QR Code sous forme d'image en base64
        const qrCodeImage = await QRCode.toDataURL(qrData);

        res.json({ userId, qrCode: qrCodeImage });
    } catch (err) {
        res.status(500).json({ error: "Erreur lors de la génération du QR Code" });
    }
});

// Démarrer le serveur
app.listen(PORT, () => {
  console.log(`Serveur démarré sur http://localhost:${PORT}`);
});
