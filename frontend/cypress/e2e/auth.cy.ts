describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/login')
  })

  it('logs in with valid credentials and redirects to chat', () => {
    cy.get('input[type="email"]').type('demo@esgadvisor.ai')
    cy.get('input[type="password"]').type('demo1234')
    cy.get('button[type="submit"]').click()

    cy.url().should('include', '/chat')
    cy.contains('ESG Mefali').should('be.visible')
    cy.contains('Nouvelle conversation').should('be.visible')
  })

  it('shows error for wrong password', () => {
    cy.get('input[type="email"]').type('demo@esgadvisor.ai')
    cy.get('input[type="password"]').type('wrongpassword')
    cy.get('button[type="submit"]').click()

    cy.url().should('include', '/login')
    cy.get('[class*="red"]').should('be.visible')
  })

  it('logs out and redirects to login', () => {
    cy.login('demo@esgadvisor.ai', 'demo1234')
    cy.visit('/chat')
    cy.contains('Nouvelle conversation').should('be.visible')

    cy.contains('Se déconnecter').click()
    cy.url().should('include', '/login')
  })
})
