type PlaceholderPageProps = {
  title: string;
};

function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <section>
      <h1 className="display-6 fw-bold mb-1">{title}</h1>
      <p className="text-body-secondary mb-0">
        This section is under construction.
      </p>
    </section>
  );
}

export default PlaceholderPage;
