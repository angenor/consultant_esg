describe('Chat', () => {
  beforeEach(() => {
    cy.login('demo@esgadvisor.ai', 'demo1234')
    cy.visit('/chat')
  })

  it('shows empty state with suggestion chips', () => {
    cy.contains('ESG Mefali').should('be.visible')
    cy.contains('Calculer mon score ESG').should('be.visible')
    cy.contains('Mon empreinte carbone').should('be.visible')
    cy.contains('Trouver des fonds verts').should('be.visible')
    cy.contains('Profil de mon entreprise').should('be.visible')
  })

  it('sends a message via suggestion chip', () => {
    cy.contains('Calculer mon score ESG').click()

    // User message should appear
    cy.contains('Calculer mon score ESG').should('be.visible')

    // Wait for assistant response to start streaming
    cy.get('[class*="assistant"], [class*="bg-white"]', { timeout: 15000 })
      .last()
      .should('not.be.empty')
  })

  it('sends a message via text input', () => {
    cy.get('textarea').type('Bonjour{enter}')

    // User message should appear
    cy.contains('Bonjour').should('be.visible')

    // Wait for assistant response
    cy.get('[class*="assistant"], [class*="bg-white"]', { timeout: 15000 })
      .last()
      .invoke('text')
      .should('have.length.gt', 10)
  })

  it('creates a new conversation via button', () => {
    cy.contains('Nouvelle conversation').click()

    cy.url().should('include', '/chat/')
    cy.get('aside').find('button').should('have.length.gte', 2)
  })
})
