const http = require('http');

describe('Express Server', () => {
  let server;

  beforeAll((done) => {
    // Start the server
    const app = require('./server');
    server = app.listen(3001, () => {
      console.log('Test server started on port 3001');
      done();
    });
  });

  afterAll((done) => {
    if (server) {
      server.close(done);
    } else {
      done();
    }
  });

  describe('GET /', () => {
    it('should return Hello World!', (done) => {
      http.get('http://localhost:3001/', (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          expect(res.statusCode).toBe(200);
          expect(data).toBe('Hello World!');
          done();
        });
      }).on('error', (err) => {
        done(err);
      });
    });

    it('should return status 200', (done) => {
      http.get('http://localhost:3001/', (res) => {
        expect(res.statusCode).toBe(200);
        done();
      }).on('error', (err) => {
        done(err);
      });
    });
  });
});