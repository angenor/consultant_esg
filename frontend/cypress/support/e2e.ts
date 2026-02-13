import './commands'

Cypress.Commands.add('login', (email: string, password: string) => {
  cy.request('POST', '/api/auth/login', { email, password }).then((resp) => {
    window.localStorage.setItem('token', resp.body.access_token)
  })
})
