const express = require('express'); 
const app = express(); 
const port = 3111; 

// щоб читати JSON
app.use(express.json());

// GET
app.get('/', (req, res) => {
    res.send('Hello Worldbbmnbm,bm,b');
});

// POST
app.delete('/data', (req, res) => {
    console.log(req.body);
    res.json({
        message: 'Дані отримано',
        data: req.body
    });
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});
