const express = require('express');

const settings = require('./config/settings');
const schema = require('./models/schema');
const routes = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

const app = express();
app.use(express.json());
app.use(routes);
app.use(errorHandler);

async function start() {
    await schema.initSchema();
    await schema.seed();
    app.listen(settings.port, () => {
        console.log(`LMS API rodando na porta ${settings.port}...`);
    });
}

if (require.main === module) {
    start();
}

module.exports = app;
