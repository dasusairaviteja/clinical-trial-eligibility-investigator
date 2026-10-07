const {test,expect}=require('@playwright/test');
test('reviewer connects, investigates, corrects, reloads and exports',async({page})=>{
  await page.goto('/');
  await page.getByLabel('Reviewer access token').fill('browser-test-only-token-not-for-deployment');
  await page.getByRole('button',{name:'Connect',exact:true}).click();
  await expect(page.locator('#identity')).toHaveText('Connected as browser-reviewer');
  await expect(page.locator('#status')).toHaveText('Synthetic demo ready.');
  await page.getByRole('button',{name:'Investigate demo case'}).click();
  await expect(page.locator('#results')).toBeVisible();
  await page.getByLabel('Reason',{exact:true}).fill('Browser test: evidence needs review');
  await page.getByRole('button',{name:'Save correction'}).click();
  await expect(page.locator('#criteria')).toContainText('Latest reviewer assertion: unknown');
  await page.getByRole('button',{name:'Refresh saved reports'}).click();
  await expect(page.locator('#history button').first()).toBeVisible();
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Download printable report'}).click();
  expect((await download).suggestedFilename()).toBe('triallens-evidence.html');
  await page.getByRole('button',{name:'Disconnect',exact:true}).click();
  await expect(page.locator('#results')).toBeHidden();
});
test('mobile layout has no horizontal overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
  await expect(page.getByRole('heading',{name:'Make every finding traceable.'})).toBeVisible();
});
